import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = pytest.mark.suite_functional_vlan

packet_vids = ["x"]  # VLAN tag number contained in the transmitted packets
vlans = {
    1: {
        "ports": [1, 2, 3],
        "pvid": True,
        "untagged": True
    },
    2: {
        "ports": [4],
        "pvid": False,
        "untagged": True
    }
}


@pytest.mark.asyncio
async def test_vlan_basic_functionality(testbed):
    f"""
    Test Name: VLAN basic functionality
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN tagged packets can be received/not received on specified port.
    Test Procedure:
    Test Procedure:
    1.Specify test data:
        - packet_vids : {packet_vids}\n
        - vlans\n {vlans}
    2.Set links to vlans.
        Verify vlans successfully added to links
    3.Map receiving and non receiving ports.
        Link 1 ->  tx_port
        Links 2-4 -> rx_ports
    4.Setup packet stream for the broadcast packet:
        src_mac = 
        dst_mac = 'ff:ff:ff:ff:ff:ff'
    5.Send traffic to rx_ports
        Verify traffic received on ports #2 and #3
        Verify traffic loss at port #4
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

    # 2.Set links to vlans.
    for vlan, setting in vlans.items():
        pvid = True if setting["pvid"] is True else ""
        is_untagged = True if setting["untagged"] is True else ""
        for port in setting["ports"]:
            out = await BridgeVlan.add(input_data=[
                {device: [{"device": f"{ports[port - 1]}", "vid": int(vlan), "pvid": pvid, "untagged": is_untagged}]}])
            assert out[0][device][
                       "rc"] == 0, f"Verify vlan : {vlan}  successfully added to link : {ports[port - 1]}\n {out}"

    # 3. Map receiving and non receiving ports. Who sends and who not
    # 4. Setup packet stream for the broadcast packet:
    # 5. Send traffic to rx_ports
    #     Verify traffic received on ports #2 and #3
    #     Verify traffic loss at port 4
