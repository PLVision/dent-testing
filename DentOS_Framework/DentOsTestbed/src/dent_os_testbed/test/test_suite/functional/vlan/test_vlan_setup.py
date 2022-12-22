import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.utils.test_utils.tb_utils import tb_get_all_devices

pytestmark = pytest.mark.suite_functional_vlan


@pytest.mark.asyncio
async def test_vlan_simple_set_up(testbed):
    """
    Test Name: VLAN setup: 4 links 2 VLANs
    Test Suite: suite_vlan_functioning
    Test Overview: Test VLAN setup
    Test Procedure:
        1. Configure a VLAN-aware bridge with 4 links
        2. Put links  swp1, swp2 into VLAN 10
        2. Put links  swp3, swp4 into VLAN 20

    """
    port_names = ["swp1", "swp2", "swp3", "swp4"]
    infra_device = await tb_get_all_devices(testbed)
    dev = infra_device[0]

    out = await IpLink.add(input_data=[{dev.host_name: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}])
    assert out[0][dev.host_name]["rc"] == 0, out
    await IpLink.set(input_data=[{dev.host_name: [{"device": "br0", "operstate": "up"}]}])
    for port in port_names:
        peer_name = port_names.index(port) + 1
        out = await IpLink.set(input_data=[{dev.host_name: [{"device": f"{port}", "operstate": "up"}]}])
        assert out[0][dev.host_name]["rc"] == 0, out
        out = await IpLink.set(input_data=[{dev.host_name: [{"device": f"veth{peer_name}", "operstate": "up"}]}])
        assert out[0][dev.host_name]["rc"] == 0, out
        await IpLink.set(input_data=[{dev.host_name: [{"device": f"{port}", "master": "br0"}]}])

    # Put links  swp1, swp2 into VLAN 10
    for swp in ["swp1", "swp2"]:
        out = await BridgeVlan.add(
            input_data=[{dev.host_name: [{"device": f"{swp}", "vid": 10, "pvid": True, "untagged": True}]}])
        assert out[0][dev.host_name]["rc"] == 0, out


    # Put links  swp3, swp4 into VLAN 20
    for swp in ["swp3", "swp4"]:
        out = await BridgeVlan.add(
            input_data=[{dev.host_name: [{"device": f"{swp}", "vid": 20, "pvid": True, "untagged": True}]}])
        assert out[0][dev.host_name]["rc"] == 0, out
