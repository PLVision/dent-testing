import pytest
import asyncio

from dent_os_testbed.test.test_suite.functional.lldp.lldp_utils import start_or_kill_lldp_service
# from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.lldp.lldp import Lldp

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic
)

pytestmark = [
    pytest.mark.suite_functional_storm_control,
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_tgen', 'cleanup_ip_addrs')
]


async def test_lldp_rx_port_down_up(testbed):
    """
    Test Name: test_lldp_rx_port_down_up
    Test Suite: suite_functional_lldp
    Test Overview: Verify that LLDP is receiving packets when the port is up and
                   dropping packets when the port is down.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init ports swp1, swp2, swp3, swp4.
    2.  Start lldp service.
    3.  Set port swp1 admin state DOWN.
    4.  Enable port swp1 trasmit lldp units.

    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 15
    # wait for the transmitting packets

    await start_or_kill_lldp_service(dent_dev, start=True)

    try:
        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': ports[0], 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'DOWN' state.\n{out}"

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'device': ports[0], 'lldp': True, 'status': 'rx-only'}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ports.\n{out}'

        out = await IpAddress.add(
            input_data=[{device_host_name: [
                {'dev': ports[0], 'prefix': '192.168.1.5/24', 'broadcast': '192.168.1.255'},
                {'dev': ports[1], 'prefix': '192.168.1.4/24', 'broadcast': '192.168.1.255'}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to add IP address to ports.\n{out}'

        address_map = (
            # swp port, tg port,    tg ip,          gw,           plen
            (ports[0], tg_ports[0], '192.168.1.6', '192.168.1.5', 24),
            (ports[1], tg_ports[1], '192.168.1.7', '192.168.1.4', 24)
        )

        dev_groups = tgen_utils_dev_groups_from_config(
            {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
            for _, port, ip, gw, plen in address_map
        )

        await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

        """
        Set up the following stream:
        — stream_A —
        swp1 -> swp2
        """

        streams = {
            'LLDP': {
                'type': 'ethernet',
                'protocol': '0x88cc',
                'frameSize': 150,
                'ip_source': dev_groups[tg_ports[1]][0]['name'],
                'ip_destination': dev_groups[tg_ports[0]][0]['name'],
                'srcMac': '92:cc:23:09:37:ca',
                'dstMac': '01:80:c2:00:00:0e',
                'rate': 5200
            }
        }

        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        import pdb
        pdb.set_trace()

        out = await Lldp.show(
            input_data=[{device_host_name: [
                {'interface': ports[0], 'neighbors': True, 'ports': True}]}], parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f'Failed to show LLDP neighbors.\n{out}'

        lldp_neighbors = out[0][device_host_name]['parsed_output']
        print(lldp_neighbors)

        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': ports[0], 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'UP' state.\n{out}"

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        out = await Lldp.show(
            input_data=[{device_host_name: [
                {'interface': ports[0], 'neighbors': True, 'ports': True}]}], parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f'Failed to show LLDP neighbors.\n{out}'

        lldp_neighbors = out[0][device_host_name]['parsed_output']
        print(lldp_neighbors)

    finally:
        await tgen_utils_stop_traffic(tgen_dev)
        out = await IpLink.set(
            input_data=[{device_host_name: [{'device': ports[0], 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'UP' state.\n{out}"
        await start_or_kill_lldp_service(dent_dev, kill=True)
