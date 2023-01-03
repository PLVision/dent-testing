import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen
from DentOS_Framework.DentOsTestbed.src.dent_os_testbed import TestBed

pytestmark = pytest.mark.suite_functional_vlan

@pytest.mark.asyncio
async def test_vlan_basic_functionality(testbed: TestBed):
    """
    Test Name: VLAN basic functionality
    Test Suite: suite_functional_vlan
    Test Overview: Test VLAN tagged packets can be received/not received on specified port.
    Test Procedure:
    1.Specify test data: packet to send, port settings: vla id, tagged/untagged etc.
        Port 1 vlan 1 pvid untagged
        Port 2 vlan 1 pvid untagged
        Port 3 vlan 1 pvid untagged
        Port 4 vlan 2 untagged

    2.Create bridge entity and set to "up" state.
        Verify bridge entity created and is set to "up" state.

    3.Create links and set state to `up`.
        Verify links are created and put to "ùp" state.

    4.Set bridge as master to links.
        Verify links enslaved to bridge

    5.Set links to vlans as specified in step #1.
        Verify vlans successfully added to links

    6. Map receiving and non receiving ports. Who sends and who not.
        Link 1 ->  tx_port
        Links 2-4 -> rx_ports

    7. Setup packet stream for the broadcast package:
        src_mac =  / tx_port mac .
        dst_mac = 'ff:ff:ff:ff:ff:ff'

    8. Clean Traffic generators  stats before sending stream.
    9. Send traffic to rx_ports
        Verify traffic received on ports #2 and #3
        Verify traffic loss at port #4
    """

    #  1.Specify test data: packet to send, port settings: vla id, tagged/untagged etc.
    packet_vids: []  # VLAN tag number contained in the transmitted packets
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


    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent eith tgn connections")
        return
    dent_dev = dent_devices[0]  # 1 девайс
    device = dent_dev.host_name  # device --  "infra_sw1"
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
        #  Verify links are created and put to "ùp" state.
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
                {device: [{"device": f"{ports[port - 1]}", "vid": vlan, "pvid": pvid, "untagged": is_untagged}]}])
            assert out[0][device][
                       "rc"] == 0, f"Verify vlan : {vlan}  successfully added to link : {ports[port - 1]}\n {out}"

    # 6. Map receiving and non receiving ports. Who sends and who not

    # 7. Setup packet stream for the broadcast package:

    # 8. Clean Traffic generators  stats before sending stream.
    # 9. Send traffic to rx_ports
    #     Verify traffic received on ports #2 and #3
    #     Verify traffic loss at port 4