import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = pytest.mark.suite_functional_vlan

packet_vids = ["x", 0, 5, 101, 500, 4094]  # VLAN tag number contained in the transmitted packets
vlans = {
    5: {
        "ports": [1, 2],
        "pvid": True,
        "untagged": True
    },
    101: {
        "ports": [1],
        "pvid": False,
        "untagged": False
    },
    "101": {
        "ports": [4],
        "pvid": True,
        "untagged": True
    },
    4094: {
        "ports": [1],
        "pvid": False,
        "untagged": True
    },
    "4094": {
        "ports": [2],
        "pvid": False,
        "untagged": False
    }
}


@pytest.mark.asyncio
async def test_switching_modes_via_cli(testbed):
    f"""
    Test Name: VLAN switching via cli
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN modes can be set -> deleted -> set
    Test Procedure:
     1.Specify test data.
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
        Verify no traffic loss on rx_ports
    6.Clean up vlan settings from ports.
        Re-initiate test params
    7. Switch between VLANs and VLAN's modes as specified by the test case
    8. Re-define RX and non-RX ports according to the VLAN configuration
    9. Re-set streams as specified by the test case
    10. Send Traffic from each of the transmitting interfaces according to the test case
    11. Verify no packet loss nor packet leak occurred and all transmitted traffic received

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
    #     Verify no traffic loss on rx_ports
    # 6. Clean up vlan settings from ports.
    #     Re-initiate test params
    # 7. Switch between VLANs and VLAN's modes as specified by the test case
    # 8. Re-define RX and non-RX ports according to the VLAN configuration
    # 9. Re-set streams as specified by the test case
    # 10. Send Traffic from each of the transmitting interfaces according to the test case
    # 11. Verify no packet loss nor packet leak occurred and all transmitted traffic received


@pytest.mark.asyncio
async def test_switching_modes_with_mac_increment(testbed):
    f"""
    Test Name: MAC increment broadcast
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN tagged packets can be received/not received on specified port.
    Test Procedure:
    1.Specify test data.
        - packet_vids : {packet_vids}\n
        - vlans\n {vlans}
    2.Set links to vlans.
        Verify vlans successfully added to links
    3.Map receiving and non receiving ports.
        Link 1 ->  tx_port
        Links 2-4 -> rx_ports
    # 4. Set up streams with incremented MAC address (14000), pps 3000 and 14000 packet per burst
    # 5. Send traffic to rx_ports
    # 6. Verify all MAC entries were learnt or re-learnt on the VLAN
    # 7. Verify no packet loss nor packet leak occurred and all transmitted traffic received
    # 8. Re-initiate test params
    # 9.Repeat steps 5 -12 for receiving ports

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
    # 4. Set up streams with incremented MAC address (14000), pps 3000 and 14000 packet per burst
    # 5. Send traffic to rx_ports
    # 6. Verify all MAC entries were learnt or re-learnt on the VLAN
    # 7. Verify no packet loss nor packet leak occurred and all transmitted traffic received
    # 8. Re-initiate test params
    # 9.Repeat steps 5 -12 for receiving ports
