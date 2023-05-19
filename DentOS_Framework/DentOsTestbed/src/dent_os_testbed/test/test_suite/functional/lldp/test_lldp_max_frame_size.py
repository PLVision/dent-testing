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


async def test_lldp_max_frame_size(testbed):
    """
    Test Name: test_lldp_max_frame_size
    Test Suite: suite_functional_lldp
    Test Overview: Verify device receiving LLDP packet with all media types and their options.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init ports swp1, swp2, swp3, swp4.
    2.  Start lldp service.
    3.  Set port swp1 admin state UP.
    4.  Enable port swp1 trasmit lldp units.
    5.  Setup Max LLDP with all options for trasmitting to swp1.
    6.  Transmitting LLDP packet to swp1.
    7.  Verifying Max LLDP packet have been received on swp1 with correct info.
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
                {'device': ports[0], 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'UP' state.\n{out}"

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'device': ports[0], 'lldp': True, 'status': 'rx-only'}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ports.\n{out}'

        out = await Lldp.show(
            input_data=[{device_host_name: [
                {'interface': ports[0], 'neighbors': True, 'ports': True}]}], parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f'Failed to show LLDP neighbors.\n{out}'

        # 5.  Setup Max LLDP with all options for trasmitting to swp1.
        # 6.  Transmitting LLDP packet to swp1.
        # 7.  Verifying Max LLDP packet have been received on swp1 with correct info.

    finally:
        await set_default_tx_interval(out, device_host_name)
        await start_or_kill_lldp_service(dent_dev, kill=True)
