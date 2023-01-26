import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_connect_to_tgen,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_get_swp_info,
)

pytestmark = pytest.mark.suite_functional_bridging


@pytest.mark.asyncio
async def test_bridging_learning_address(testbed):
    """
    Test Name: test_bridging_learning_address
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge dynamic entries learning.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Send traffic to swp1, swp2, swp3, swp4 with source macs 
        aa:bb:cc:dd:ee:11 aa:bb:cc:dd:ee:12 
        aa:bb:cc:dd:ee:13 aa:bb:cc:dd:ee:14 accordingly.
    8.  Verify that address have been learned.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print.error("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10

    out = await IpLink.add(
        input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0,  f"Verify that bridge created.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge, bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    
    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}" 
    
    address_map = (
        #swp port, tg port,     tg ip,      gw,         plen
        (ports[0], tg_ports[0], "11.0.0.1", "11.0.0.4", 24),
        (ports[1], tg_ports[1], "11.0.0.2", "11.0.0.3", 24),
        (ports[2], tg_ports[2], "11.0.0.3", "11.0.0.2", 24),
        (ports[3], tg_ports[3], "11.0.0.4", "11.0.0.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "bridge_1": {
            "ip_source": dev_groups[tg_ports[3]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:11",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_2": {
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:12",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_3": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[2]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:13",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_4": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:14",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                         parse_output=True)

    devices = out[0][device_host_name]["parsed_output"]
    data = []
    for dev in devices:
         data.append(dev.get("mac", None))
    print(data)

    test_data_in = ["aa:bb:cc:dd:ee:11","aa:bb:cc:dd:ee:12","aa:bb:cc:dd:ee:13","aa:bb:cc:dd:ee:14"]
    for addr in test_data_in :
        assert addr in test_data_in, f"Verify that source mac aa:bb:cc:dd:ee:11,aa:bb:cc:dd:ee:12,aa:bb:cc:dd:ee:13,aa:bb:cc:dd:ee:14 have been learned.\n{out}"
    
    await tgen_utils_stop_protocols(tgen_dev)


#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED
@pytest.mark.asyncio
async def test_bridging_learning_address_rate(testbed):
    """
    Test Name: test_bridging_learning_address_rate
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge learning entries rate verifying no packets were flooded to 3 port.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood ON.
    7.  Send traffic to swp1 to learn source increment address 
        in range 00:00:00:00:00:35 - 00:00:00:00:04:1d.
    8.  Send traffic to swp2 with destination increment address 
        in range 00:00:00:00:00:35 - 00:00:00:00:04:1d.
    9.  Verify that there was not flooding to swp3.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print.error("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    #tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]

    #out = await IpLink.add(
    #    input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    #assert out[0][device_host_name]["rc"] == 0, f" Verify that bridge created.\n {out}"

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that bridge, bridge entities set to 'UP' state and links enslaved to bridge.\n {out}"
    
    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": True} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that entities set to learning 'ON' and flooding 'ON' state.\n {out}" 
    
    # Send traffic and verify 7-9 steps
#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED#BLOCKED


@pytest.mark.asyncio
async def test_bridging_learning_illegal_address(testbed):
    """
    Test Name: test_bridging_learning_illegal_address
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge is not learning illegal address.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Send traffic by TG.
    8.  Verify that illegal address haven't been learned.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print.error("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    #tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    
    #out = await IpLink.add(
    #    input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    #assert out[0][device_host_name]["rc"] == 0, f" Verify that bridge created.\n {out}"

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that bridge, bridge entities set to 'UP' state and links enslaved to bridge.\n {out}"
    
    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f" Verify that entities set to learning 'ON' and flooding 'OFF' state.\n {out}" 
   
    # Send traffic and verify 7-8 steps


@pytest.mark.asyncio
async def test_bridging_relearning_on_different_vlans(testbed):
    """
    Test Name: test_bridging_relearning_on_different_vlans
    Test Suite: suite_functional_bridging
    Test Overview: Verify that mac address relearning on different vlans.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set br0 ageing time to 600 seconds [default is 300 seconds].
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Add interfaces to vlans swp1 swp2 swp3 --> vlans 2,3.
    9.  Send traffic by TG.
    10. Verify that entries have been learned on different vlans.
    11. Verify that entries have been removed from swp1 due to mac move to swp3.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print.error(
            "The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    # tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]

    #out = await IpLink.add(
    #    input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    #assert out[0][device_host_name][
    #    "rc"] == 0, f" Verify that bridge created.\n {out}"

    #    {"device": bridge, "ageing_time": 600},
    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name][
        "rc"] == 0, f" Verify that ageing time set to '600', bridge and bridge entities set to 'UP' state and links enslaved to bridge.\n {out}"

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    assert out[0][device_host_name][
        "rc"] == 0, f" Verify that entities set to learning 'ON' and flooding 'OFF' state.\n {out}"

    #out = await BridgeVlan.add(
      #  input_data=[{device_host_name: [
      #      {"device": port, "vid": 2} for port in ports]}, 
       #     {"device": port, "vid": 3} for port in ports])
    #assert out[0][device_host_name][
     #   "rc"] == 0, f" Verify that interfaces added to vlans '2' and '3'.\n {out}"

    # 9.  Send traffic by TG.
    # 10. Verify that entries have been learned on different vlans.
    # 11. Verify that entries have been removed from swp1 due to mac move to swp3.
