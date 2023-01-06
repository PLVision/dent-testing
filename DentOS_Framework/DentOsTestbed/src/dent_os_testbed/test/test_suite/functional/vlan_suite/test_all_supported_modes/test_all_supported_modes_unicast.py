import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = pytest.mark.suite_functional_vlan

@pytest.mark.asyncio
async def test_all_supported_modes_unicast(testbed):
    """
    Test Name: Unicast with all modes supported
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN with unicast when all modes supported
    Test Procedure:
    1.Specify test data: packet to send, port settings: vla id, tagged/untagged etc.
        Port 1 vlan 2 tagged, 3 untagged,4 pvid untagged
        Port 2 vlan 2 tagged
        Port 3 vlan 3 pvid untagged
        Port 4 vlan 4 pvid untagged

    2.Create bridge entity and set state to "up" state.
        Verify bridge entity created and is set to "up" state.

    3.Create links and set state to `up`.
        Verify links are created and put to "ùp" state.

    4.Set bridge as master to links.
        Verify links enslaved to bridge

    5.Set links to vlans as specified in step #1.
        Verify vlans successfully added to links

    6. Map receiving and non receiving ports.
        Port 1 ->  tx_port
        Ports 4 -> rx_ports

    7. Setup packet stream(s) for the broadcast package:
        src_mac =
        dst_mac = ?

    8. Clean Traffic generators  stats before sending stream.

    9. Send traffic to rx_ports
        Verify:
         traffic with vlan "x" received on port 4
         traffic with vlan "1" received on port 2
         traffic with vlan "2" received on port 1, 2
         traffic with vlan "3" received on port 1, 3
         traffic with vlan "4" received on port 1, 4

    """

    #  1.Specify test data: packet to send, port settings: vla id, tagged/untagged etc.
    packet_vids = ['x', 1, 2, 3, 4]  # VLAN tag number contained in the transmitted packet
    vlans = {
        2: {
            "ports": [1, 2],
            "pvid": False,
            "untagged": False
        },
        3: {
            "ports": [1],
            "pvid": False,
            "untagged": True
        },
        "3": {
            "ports": [3],
            "pvid": True,
            "untagged": True
        },
        4: {
            "ports": [1, 4],
            "pvid": True,
            "untagged": True
        }
    }

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    dent_dev = dent_devices[0]
    device = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device][0]
    ports = tgen_dev.links_dict[device][1]

    #  2.Create bridge entity and set state to "up" state.
    out = await IpLink.add(input_data=[{device: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}])
    assert out[0][device]["rc"] == 0, f"Verify bridge entity created.\n {out}"

    await IpLink.set(input_data=[{device: [{"device": "br0", "operstate": "up"}]}])
    assert out[0][device]["rc"] == 0, f"Verify bridge entity set to 'up' state.\n {out}"

    #  3.Create links and set state to `up`.
    for port in ports:
        await IpLink.add(input_data=[{device: [{"device": f"{port}"}]}])
        out = await IpLink.set(input_data=[{device: [{"device": f"{port}", "operstate": "up"}]}])
        assert out[0][device]["rc"] == 0, f"Verify links are created and put to 'up' state.\n {out}"

    # 4.Set bridge as master to links.
    for port in ports:
        await IpLink.set(input_data=[{device: [{"device": f"{port}", "master": "br0"}]}])
        assert out[0][device]["rc"] == 0, f" Verify links enslaved to bridge.\n {out}"

    # 5. Set links to vlans as specified in step #1.
    for vlan, setting in vlans.items():
        pvid = True if setting["pvid"] is True else ""
        is_untagged = True if setting["untagged"] is True else ""
        for port in setting["ports"]:
            out = await BridgeVlan.add(input_data=[
                {device: [{"device": f"{ports[port - 1]}", "vid": int(vlan), "pvid": pvid, "untagged": is_untagged}]}])
            assert out[0][device][
                       "rc"] == 0, f"Verify vlan : {vlan}  successfully added to link : {ports[port - 1]}\n {out}"

    # 6. Map receiving and non receiving ports. Who sends and who not
    # 7. Setup packet stream for the broadcast package with specified packet_vids :
    # 8. Clean Traffic generators  stats before sending stream.
    # 9. Send traffic to rx_ports
