import pytest
import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.lldp.lldp import Lldp

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen
from dent_os_testbed.test.test_suite.functional.lldp.lldp_utils import (
    verify_lldp_pck_count,
    set_default_tx_interval,
    start_or_kill_lldp_service
)

pytestmark = [
    pytest.mark.suite_functional_lldp,
    pytest.mark.asyncio
]


async def test_lldp_tx_port_down_up(testbed):
    """
    Test Name: test_lldp_tx_port_down_up
    Test Suite: suite_functional_lldp
    Test Overview: Verify LLDP transmits packets when the port is up,
                   and packets are not transmitted when the port is down.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init ports swp1, swp2, swp3, swp4.
    2.  Start lldp service.
    3.  Set port swp1 admin state DOWN.
    4.  Enable port swp1 trasmit lldp units.
    5.  Configure tx-interval to 2 sec.
    6.  Verifying that no LLDP packets have been transmitted due to port swp1 being down.
    7.  Set port swp1 admin state UP.
    8.  Verifying that LLDP packets have been transmitted due to port swp1 being up.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    ports = tgen_dev.links_dict[device_host_name][1]
    # wait for the transmitting packets
    wait = 30

    await start_or_kill_lldp_service(dent_dev, start=True)

    try:
        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': ports[0], 'operstate': 'down'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'DOWN' state.\n{out}"

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'device': ports[0], 'lldp': True, 'status': 'tx-only'},
                {'lldp': True, 'tx-interval': 2}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ports and tx-interval.\n{out}'

        # verify LLDP packets count
        await verify_lldp_pck_count(out, device_host_name, exp_count=0, port=ports[0])

        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': ports[0], 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'UP' state.\n{out}"

        # wait for the transmitting packets
        await asyncio.sleep(wait)

        # verify LLDP packets count
        await verify_lldp_pck_count(out, device_host_name, exp_count=14, port=ports[0])
    finally:
        out = await IpLink.set(
            input_data=[{device_host_name: [{'device': ports[0], 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'UP' state.\n{out}"

        await set_default_tx_interval(out, device_host_name)
        await start_or_kill_lldp_service(dent_dev, kill=True)
