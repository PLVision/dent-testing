import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = pytest.mark.suite_functional_vlan

packet_vids = ['x', 1, 2]  # VLAN tag number contained in the transmitted packet
vlans = {
    1: {
        "ports": [1, 2, 3, 4],
        "pvid": True,
        "untagged": True
    }
}


@pytest.mark.asyncio
async def test_default_config_broadcast(testbed):
    f"""
    Test Name: Broadcast with default configuration
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN default configuration with broadcast packet
    Test Procedure:
    1.Specify test data.
        - packet_vids : {packet_vids}\n
        - vlans\n {vlans}
    2.Set links to vlans.
        Verify vlans successfully added to links
    3.Map receiving and non receiving ports.
        Port 1 ->  tx_port
        Ports 2-4 -> rx_ports
    4.Setup packet stream(s) for the broadcast packet:
        src_mac =  / tx_port mac .
        dst_mac = 'ff:ff:ff:ff:ff:ff'
    5.Send traffic to rx_ports
        Verify traffic received on ports #2 ,3, 4  with no VID tag in packet

    """

    # TODO How to find out src MAC address of the packet
    # TODO How to clean up previous configuration
    # TODO How to clean port stats
    # TODO How to set multiple stream with different VID's
    # TODO How to clean up previous configuration
    # TODO how to assign mac address to ports

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
    # 4. Setup packet stream for the broadcast packet with specified packet_vids.
    # 5. Send traffic to rx_ports
    #     Verify traffic received on ports #2 ,3, 4  with no VID tag in packet


@pytest.mark.asyncio
async def test_default_config_multicast(testbed):
    f"""
    Test Name: Multicast with default configuration
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN default configuration with multicast packet
    Test Procedure:
    1.Specify test data.
        - packet_vids : {packet_vids}\n
        - vlans\n {vlans}
    2.Set links to vlans.
        Verify vlans successfully added to links
    3.Map receiving and non receiving ports.
        Link 1 ->  tx_port
        Links 2-4 -> rx_ports
    4.Setup packet stream for the multicast packet.
        src_mac = 
        dst_mac = "01:00:5E:00:00:C8"
    5.Send traffic to rx_ports
        Verify traffic received on ports #2 ,3, 4  with no VID in packet
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

    # 3.Map receiving and non receiving ports.
    # 4.Setup packet stream for the multicast packet.
    # 5.Send traffic to rx_ports
    #     Verify traffic received on ports #2, 3, 4


@pytest.mark.asyncio
async def test_default_config_unicast(testbed):
    f"""
    Test Name: Unicast with default configuration
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN default configuration with unicast
    Test Procedure:
    1.Specify test data.
        - packet_vids : {packet_vids}\n
        - vlans\n {vlans}
    2.Set links to vlans.
        Verify vlans successfully added to links
    3.Map receiving and non receiving ports.
        Link 1 ->  tx_port
        Links 2 -> rx_ports
    4.Setup packet stream for the unicast packet.
        src_mac = ?
        dst_mac = ?
    5.Send traffic to rx_ports
        Verify traffic received on ports #2  with no VID in packet
        Verify traffic NOT received on ports #3, 4
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

    # 3. Map receiving and non receiving ports.
    # 4. Setup packet stream for the unicast packet.
    # 5. Send traffic to rx_ports
    #     Verify traffic received on ports #2  with no VID in packet
    #     Verify traffic NOT received on ports #3, 4


@pytest.mark.asyncio
async def test_default_config_uknown_unicast(testbed):
    f"""
    Test Name: Unknown unicast with default configuration
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN default configuration with unknown unicast
    Test Procedure:
    1.Specify test data.
        - packet_vids : {packet_vids}\n
        - vlans\n {vlans}
    2.Set links to vlans.
        Verify vlans successfully added to links
    3.Map receiving and non receiving ports.
        Link 1 ->  tx_port
        Links 2 -> rx_ports
    4.Setup packet stream for the unicast packet.
        src_mac = ?
        dst_mac = ?
    5.Send traffic to rx_ports
        Verify traffic received on ports #2, 3, 4.
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
    # Most probably we need to
    #  - clear FDB and after send unicast
    #  - Other way  resolve ARP by flooding all ports and after send unicast to wrong MAC
    # 3. Map receiving and non receiving ports.
    # 4. Setup packet stream for the unicast packet.
    # 5. Send traffic to rx_ports
    #     Verify traffic received on ports #2 , 3, 4.
