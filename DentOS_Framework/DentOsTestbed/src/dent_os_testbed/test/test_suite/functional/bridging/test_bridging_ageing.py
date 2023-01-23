import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect
)

pytestmark = pytest.mark.suite_functional_bridging


@pytest.mark.asyncio
async def test_bridging_ageing_refresh(testbed):
    """
    Test Name: test_bridging_ageing_refresh
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge ageing time refreshes after re-sending traffic.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set br0 ageing time to 40 seconds [default is 300 seconds].
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Send traffic to swp1 with sourse mac aa:bb:cc:dd:ee:11.
    9.  Delaying for 50 seconds.
    10. Send traffic to swp1 again with sourse mac aa:bb:cc:dd:ee:11 for refreshing br0 
        ageing time to be set back to 40 seconds for that entry.
    11. Delaying for 20 seconds.
    12. Verify that entry exist.
    13. Delaying for 50 seconds.
    14. Verify that entry doesn't exist due to expired ageing time for that entry.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10

    out = await IpLink.add(
    input_data=[{device_host_name: [{"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge created.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": bridge, "ageing_time": 40},
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that ageing time set to '40', bridge and bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"        
    
    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"

    address_map = (
        #swp port, tg port,     tg ip,      gw          plen
        (ports[0], tg_ports[0], "11.0.0.1", "11.0.0.2", 24),
        (ports[1], tg_ports[1], "11.0.0.2", "11.0.0.1", 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "bridge": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:11",
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

    await asyncio.sleep(50)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)

    await asyncio.sleep(20)

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                         parse_output=True)

    devices = out[0][device_host_name]["parsed_output"]
    data_in = []
    for dev in devices: 
         data_in.append(dev.get("mac", None))
    print(data_in)     
    assert "aa:bb:cc:dd:ee:11" in data_in, f"Verify that entry exist.\n{out}"

    await asyncio.sleep(50)

    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                         parse_output=True)

    devices = out[0][device_host_name]["parsed_output"]
    data_out = []
    for dev in devices: 
         data_out.append(dev.get("mac", None))
    print(data_out)     
    assert "aa:bb:cc:dd:ee:11" not in data_out, f"Verify that entry doesn't exist due to expired ageing time for that entry.\n{out}"

    await tgen_utils_stop_protocols(tgen_dev)


@pytest.mark.asyncio
async def test_bridging_ageing_under_continue(testbed):
    """
    Test Name: test_bridging_ageing_under_continue
    Test Suite: suite_functional_bridging
    Test Overview: Verify that bridge learning entries appear with continues traffic after ageing time expired.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set br0 ageing time to 10 seconds [default is 300 seconds].
    3.  Set ports swp1, swp2, swp3, swp4 master br0.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Continues traffic sending to swp1, swp2, swp3, swp4 with sourse macs 
        aa:bb:cc:dd:ee:11 aa:bb:cc:dd:ee:12 aa:bb:cc:dd:ee:13 aa:bb:cc:dd:ee:14 accordingly.
    9.  Delaying for 10 seconds.
    10. Verify that entries exist due to continues traffic.
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
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge created.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name:  [
            {"device": bridge, "ageing_time": 10},
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that ageing time set to '10', bridge and bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    
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
    
    await asyncio.sleep(10)
    
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
        assert addr in test_data_in, f"Verify that entries exist due to continues traffic.\n{out}"

    await tgen_utils_stop_protocols(tgen_dev)
