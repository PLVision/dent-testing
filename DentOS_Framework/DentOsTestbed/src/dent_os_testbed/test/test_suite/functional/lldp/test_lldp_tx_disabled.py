import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.lldp.lldp import Lldp

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen
from dent_os_testbed.test.test_suite.functional.lldp.lldp_utils import (
    verify_lldp_pkt_count,
    set_default_tx_interval,
    start_or_kill_lldp_service
)

pytestmark = [
    pytest.mark.suite_functional_lldp,
    pytest.mark.asyncio
]


async def test_lldp_tx_disabled(testbed):
    """
    Test Name: test_lldp_tx_disabled
    Test Suite: suite_functional_lldp
    Test Overview: Verify that LLDP tx is disabled and no LLDP packets have been transmitted.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init ports swp1, swp2, swp3, swp4.
    2.  Start lldp service.
    3.  Set port swp1 admin state UP.
    4.  Disable lldp for swp1.
    5.  Configure tx-interval to 2 sec.
    6.  Verifying that no LLDP packets have been transmitted.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    ports = tgen_dev.links_dict[device_host_name][1]
    # wait for the transmitting packets
    wait = 10

    await start_or_kill_lldp_service(dent_dev, start=True)

    try:
        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': ports[0], 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'UP' state.\n{out}"

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'device': ports[0], 'lldp': True, 'status': 'disabled'},
                {'lldp': True, 'tx-interval': 2}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ports and tx-interval.\n{out}'

        # wait for the transmitting packets
        await asyncio.sleep(wait)

        # verify LLDP packets count
        await verify_lldp_pkt_count(out, device_host_name, exp_count=1, port=ports[0])

    finally:
        await set_default_tx_interval(out, device_host_name)
        await start_or_kill_lldp_service(dent_dev, kill=True)
