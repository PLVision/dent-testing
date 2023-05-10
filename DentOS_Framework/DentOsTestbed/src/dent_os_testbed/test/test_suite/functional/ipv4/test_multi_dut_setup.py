import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

pytestmark = [
    pytest.mark.suite_functional_ipv4,
    pytest.mark.usefixtures('cleanup_bridges'),
    pytest.mark.asyncio,
]


async def test_multi_dut_setup(testbed):
    num_of_ports = 4
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], num_of_ports)
    if not tgen_dev or not dent_devices or len(dent_devices) < 2:
        pytest.skip('The testbed does not have enough dent with tgen connections')

    traffic_duration = 10
    wait_for_stats = 5
    bridge = 'br0'

    # add 2 bridges to 2 devices
    out = await IpLink.add(input_data=[{
        dent.host_name: [{'name': bridge, 'type': 'bridge'}]
        for dent in dent_devices
    }])
    assert all(res[dent]['rc'] == 0 for res in out for dent in res), 'Failed to add bridge'

    # add all ports to bridges
    out = await IpLink.set(input_data=[{
        dent.host_name: [
            {'device': port, 'operstate': 'up', 'master': bridge}  # links between devices
            for port, *_ in dent.links
        ] + [
            {'device': port, 'operstate': 'up', 'master': bridge}  # links to TG
            for port in tgen_dev.links_dict[dent.host_name][1]
        ] + [
            {'device': bridge, 'operstate': 'up'}  # bridge
        ] for dent in dent_devices
    }])
    assert all(res[dent]['rc'] == 0 for res in out for dent in res), 'Failed to enslave ports'

    # setup interfaces on TG
    tg_ports = [tg for dent in dent_devices for tg in tgen_dev.links_dict[dent.host_name][0]]
    dut_ports = [swp for dent in dent_devices for swp in tgen_dev.links_dict[dent.host_name][1]]
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': tg,
         'ip': '1.1.1.1',  # don't care
         'gw': '2.2.2.2',  # don't care
         'plen': 24}
        for tg in tg_ports
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # setup streams
    streams = {
        f'{tg_ports[0]} -> all': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'rate': 10000,  # pps
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    await asyncio.sleep(wait_for_stats)
    stats = await tgen_utils_get_traffic_stats(tgen_dev, 'Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'
