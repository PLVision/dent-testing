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


async def test_lldp_transmitted_mandatory_tlvs(testbed):
    """
    Test Name: test_lldp_transmitted_mandatory_tlvs
    Test Suite: suite_functional_lldp
    Test Overview: Verify LLDP transmitted packet with mandatory tlvs fields and OUI.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init ports swp1, swp2, swp3, swp4.
    2.  Start lldp service.
    3.  Set port swp1 admin state UP.
    4.  Enable port swp1 trasmit lldp units.
    5.  Configure tx-interval to 2 sec.
    6.  Filter lldp packet for swp1.
    7.  Verifying lldp packet captured for swp1 with mandatory tlvs fields.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    ports = tgen_dev.links_dict[device_host_name][1]
    # wait for the transmitting packets

    await start_or_kill_lldp_service(dent_dev, start=True)

    try:
        out = await IpLink.set(
            input_data=[{device_host_name: [
                {'device': ports[0], 'operstate': 'up'}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Verify that entitie set to 'UP' state.\n{out}"

        out = await Lldp.configure(
            input_data=[{device_host_name: [
                {'device': ports[0], 'lldp': True, 'status': 'tx-only'},
                {'lldp': True, 'tx-interval': 2}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to configure ports and tx-interval.\n{out}'

        rc, out = await dent_dev.run_cmd('uname -n')
        assert rc == 0, f"Failed to run command 'uname -n'.\n{out}"

        out = await Lldp.show(
            input_data=[{device_host_name: [
                {'chassis': 'True', 'cmd_options': '-f json'}]}])
        assert out[0][device_host_name]['rc'] == 0, f'Failed to show local-chassis.\n{out}'

        rc, out = await dent_dev.run_cmd(f'cat /sys/class/net/{ports[0]}/address')
        assert rc == 0, f'Failed to cat.\n{out}'

    finally:
        await set_default_tx_interval(out, device_host_name)
        await start_or_kill_lldp_service(dent_dev, kill=True)
