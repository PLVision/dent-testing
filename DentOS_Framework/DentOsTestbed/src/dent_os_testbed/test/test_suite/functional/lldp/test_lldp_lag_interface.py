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
    pytest.mark.asyncio,
    pytest.mark.usefixtures('cleanup_bonds')
]


async def test_lldp_lag_interface(testbed):
    """
    Test Name: test_lldp_lag_interface
    Test Suite: suite_functional_lldp
    Test Overview: Verify LLDP receive-transmit packet slaved interface.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Init ports swp1, swp2, swp3, swp4.
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Start lldp service.
    5.  Set port swp1 and bridge br0 admin state UP.
    6.  Configure tx-interval to 2 sec.
    7.  Filter lldp packet for swp1.
    8.  Enable lldp for swp1 rx-and-tx.
    9.  Setup LLDP packet for trasmitting to swp1.
    10. Transmitting LLDP packet to swp1.
    11. Verifying LLDP packet received and captured for swp1.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    ports = tgen_dev.links_dict[device_host_name][1]

    out = await IpLink.add(
            input_data=[{device_host_name: [
                {'device': 'bond1', 'type': 'bond mode 802.3ad'}]}])
    err_msg = f"Verify that bond1 created and type set to 'bond mode 802.3ad'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.show(
            input_data=[{device_host_name: [
                {'type': 'bond', 'device': 'bond1'}]}])
    err_msg = f"Verify that bond1 created and type set to 'bond mode 802.3ad'.\n{out}"
    assert out[0][device_host_name]['rc'] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': ports[0], 'operstate': 'down'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that swp1 set to admin state 'DOWN'.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': ports[0], 'master': 'bond1'}]}])
    assert out[0][device_host_name]['rc'] == 0, f'Verify that swp1 entitie enslaved to bond1.\n{out}'

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {'device': 'bond1', 'operstate': 'up'},
            {'device': ports[0], 'operstate': 'up'}]}])
    assert out[0][device_host_name]['rc'] == 0, f"Verify that bridge and entitie set to 'UP' state.\n{out}"

    await start_or_kill_lldp_service(dent_dev, start=True)

    try:

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'lldp': True, 'tx-interval': 2}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure tx-interval.\n{out}'

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'system': 'bond-slave-src-mac-type', 'real': True}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure system.\n{out}'

        rc, out = await dent_dev.run_cmd(f'cat /sys/class/net/{ports[0]}/address')
        assert rc == 0, f'Failed to cat.\n{out}'

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'device': ports[0], 'lldp': True, 'status': 'rx-and-tx'}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure port.\n{out}'

        out = await Lldp.show(
            input_data=[{device_host_name: [
                {'interface': ports[0], 'neighbors': True, 'ports': True}]}], parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f'Failed to show LLDP neighbors.\n{out}'

        # 9.  Setup LLDP packet for trasmitting to swp1.
        # 10. Transmitting LLDP packet to swp1.
        # 11. Verifying LLDP packet received and captured for swp1.

    finally:
        await set_default_tx_interval(out, device_host_name)
        await start_or_kill_lldp_service(dent_dev, kill=True)
