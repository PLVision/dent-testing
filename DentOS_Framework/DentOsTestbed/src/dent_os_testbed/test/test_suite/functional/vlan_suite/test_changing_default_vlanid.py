import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = pytest.mark.suite_functional_vlan

packet_vids = ["x", 2, 4094]  # VLAN tag number contained in the transmitted packet
vlans = {
    4094: {
        "ports": [1, 2, 3, 4],
        "pvid": True,
        "untagged": True
    },
}


@pytest.mark.asyncio
async def test_changing_default_vlan(testbed):
    f"""
    Test Name: Changing default VLAN Id
    Test Suite: suite_functional_vlan
    Test Overview: Test tagged packet is bigger than untagge
    Test Procedure:
    1.Specify test data.
        - packet_vids : {packet_vids}\n
        - vlans\n {vlans}
    2.Clear default VLAN ID on interfaces and set it to 4094
    3.Set links to vlans.
        Verify vlans successfully added to links
    4.Map receiving and non receiving ports.
        Link 1 ->  tx_port
        Links 2-4 -> rx_ports
    5.Setup packet stream for the broadcast packet
        src_mac =
        dst_mac = 'ff:ff:ff:ff:ff:ff'
    6.Send traffic to rx_ports
    """

    # 1.Specify test data.
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    dent_dev = dent_devices[0]
    device = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device][0]
    ports = tgen_dev.links_dict[device][1]

    # 2. Clear default VLAN ID on interfaces and set it to 4094
    out = await BridgeVlan.delete(input_data=[{device: [{"device": f"{port}", "vid": 1} for port in ports]}])
    assert out[0][device]["rc"] == 0, f"Successfully deleted default vlan from {ports} interfaces\n {out}"
    out = await BridgeVlan.set(
        input_data=[{device: [{"device": f"{port}", "vid": 4094, "pvid": True, "untagged": True} for port in ports]}])
    assert out[0][device]["rc"] == 0, f"Successfully added default vlan 4094 to {ports} interfaces\n {out}"

    # 3.Set links to vlans.
    for vlan, setting in vlans.items():
        pvid = True if setting["pvid"] is True else ""
        is_untagged = True if setting["untagged"] is True else ""
        for port in setting["ports"]:
            out = await BridgeVlan.add(input_data=[
                {device: [{"device": f"{ports[port - 1]}", "vid": int(vlan), "pvid": pvid, "untagged": is_untagged}]}])
            assert out[0][device][
                       "rc"] == 0, f"Verify vlan : {vlan}  successfully added to link : {ports[port - 1]}\n {out}"

    # 4. Map receiving and non receiving ports. Who sends and who not
    # 5. Setup packet stream for the multicast packet:
    # 6. Send traffic to rx_ports
