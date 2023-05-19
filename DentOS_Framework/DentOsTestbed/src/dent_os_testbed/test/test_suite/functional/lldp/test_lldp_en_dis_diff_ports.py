import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.lldp.lldp import Lldp

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen
from dent_os_testbed.test.test_suite.functional.lldp.lldp_utils import (
    set_default_tx_interval,
    start_or_kill_lldp_service
)

pytestmark = [
    pytest.mark.suite_functional_lldp,
    pytest.mark.asyncio
]


async def test_lldp_en_dis_diff_ports(testbed):
    """
    Test Name: test_lldp_en_dis_diff_ports
    Test Suite: suite_functional_lldp
    Test Overview: Verify LLDP receive-transmit packet slaved interface.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init ports swp1, swp2, swp3, swp4.
    2.  Start lldp service.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Configure tx-interval to 2 sec.
    5.  Filter lldp packet for swp1, swp2, swp3, swp4 ports.
    6.  LLDP:
        - Disable for swp1;
        - Enable for swp2;
        - Disable for swp3;
        - Enable for swp4.
    7.  Setup LLDP packet for trasmitting to swp1.
    8.  Transmitting LLDP packet to swp1, swp2, swp3, swp4.
    9.  Verifying LLDP packet received or dropped for swp1, swp2, swp3, swp4.
    10. Verifying LLDP packet captured for swp1, swp2, swp3, swp4.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    ports = tgen_dev.links_dict[device_host_name][1]

    await start_or_kill_lldp_service(dent_dev, start=True)

    try:
        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': port, 'operstate': 'up'} for port in ports]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entities set to 'UP' state.\n{out}"

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'lldp': True, 'tx-interval': 2}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure tx-interval.\n{out}'

        for port in ports:
            rc, out = await dent_dev.run_cmd(f'cat /sys/class/net/{port}/address')
            assert rc == 0, f'Failed to cat.\n{out}'

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'device': ports[0], 'lldp': True, 'status': 'disabled'},
                {'device': ports[1], 'lldp': True, 'status': 'rx-and-tx'},
                {'device': ports[2], 'lldp': True, 'status': 'disabled'},
                {'device': ports[3], 'lldp': True, 'status': 'rx-and-tx'}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ports.\n{out}'

        # 7.  Setup LLDP packet for trasmitting to swp1.
        # 8.  Transmitting LLDP packet to swp1, swp2, swp3, swp4.
        # 9.  Verifying LLDP packet received or dropped for swp1, swp2, swp3, swp4.
        # 10. Verifying LLDP packet captured for swp1, swp2, swp3, swp4.

        out = await Lldp.show(
            input_data=[{device_host_name: [
                {'interface': port, 'neighbors': True, 'ports': True} for port in ports]}], parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f'Failed to show LLDP neighbors.\n{out}'

    finally:
        await set_default_tx_interval(out, device_host_name)
        await start_or_kill_lldp_service(dent_dev, kill=True)
