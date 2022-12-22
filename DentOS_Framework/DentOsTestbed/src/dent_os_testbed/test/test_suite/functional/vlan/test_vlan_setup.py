import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

pytestmark = pytest.mark.suite_vlan_functioning


@pytest.mark.asyncio
async def test_vlan_simple_set_up(testbed):
    """
    Test Name: VLAN setup: 4 links 2 VLANs
    Test Suite: suite_vlan_functioning
    Test Overview: Test VLAN setup
    Test Procedure:
    1. Configure a VLAN-aware bridge with 4 links
    2. Put links into different VLANs

    """

    links = [10, 20, 30, 40]
    dev = testbed.devices[0]
    veth_pairs = {}

    out = await IpLink.add(input_data=[{dev.host_name: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}])
    assert out[0][dev.host_name]["rc"] == 0, out
    await IpLink.set(input_data=[{dev.host_name: [{"device": "br0", "operstate": "up"}]}])
    for link_beg, link_end in enumerate(links):
        out = await IpLink.add(input_data=[{dev.host_name: [{"name": f"veth{link_end}", "type": "veth"}]}])
        assert out[0][dev.host_name]["rc"] == 0, out
        await IpLink.set(input_data=[{dev.host_name: [{"device": f"veth{link_end}", "operstate": "up"}]}])
        assert out[0][dev.host_name]["rc"] == 0, out
        await IpLink.set(input_data=[{dev.host_name: [{"device": f"veth{link_beg}", "operstate": "up"}]}])
        assert out[0][dev.host_name]["rc"] == 0, out
        await IpLink.set(input_data=[{dev.host_name: [{"device": f"veth{link_end}", "master": "br0"}]}])
        assert out[0][dev.host_name]["rc"] == 0, out
        if link_end in [10, 20]:
            out = await BridgeVlan.add(
                input_data=[
                    {dev.host_name: [{"device": f"veth{link_end}", "vid": 10, "pvid": True, "untagged": True}]}])
            assert out[0][dev.host_name]["rc"] == 0, out
            await BridgeVlan.delete(
                input_data=[
                    {dev.host_name: [{"device": f"veth{link_end}", "vid": 1, "untagged": True}]}])
        else:
            out = await BridgeVlan.add(
                input_data=[
                    {dev.host_name: [{"device": f"veth{link_end}", "vid": 20, "pvid": True, "untagged": True}]}])
            await BridgeVlan.delete(
                input_data=[
                    {dev.host_name: [{"device": f"veth{link_end}", "vid": 1, "untagged": True}]}])

            assert out[0][dev.host_name]["rc"] == 0, out
        veth_pairs[f"veth{link_beg}"] = f"veth{link_end}"
