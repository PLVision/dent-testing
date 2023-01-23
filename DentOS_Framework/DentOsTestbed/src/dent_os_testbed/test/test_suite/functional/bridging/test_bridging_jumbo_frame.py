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
async def test_bridging_frame_max(testbed):
    """
    Test Name: test_bridging_frame_max
    Test Suite: suite_functional_bridging
    Test Overview: Verifying that Jambo frames of max size are learned and forwarded.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set max jumbo frame MTU size support on ports swp1, swp2, swp3, swp4.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning OFF.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Adding FDB static entries for ports swp1, swp2, swp3, swp4.
    9.  Send traffic from swp1 to swp2.
    10. Send traffic from swp3 to swp4.
    11. Send traffic from swp4 to swp3.
    12. Send traffic from swp2 to swp1.
    10. Verify that address have been learned and forwarded.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print.error(
            "The testbed does not have enough dent with tgen connections")
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
            {"device": port, "master": "br0", "operstate": "up", "mtu": 9500} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge, bridge entities set to 'UP' state, links enslaved to bridge and max jumbo frame size set to '9500'.\n{out}"

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": False, "flood": False} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that entities set to learning 'OFF' and flooding 'OFF' state.\n{out}"
    
    out = await BridgeFdb.add(
        input_data=[{device_host_name: [
            {"device": ports[0], 'lladdr':'cc:f4:ed:5b:15:39'},
            {"device": ports[1], 'lladdr':'fd:64:8a:62:27:8a'},
            {"device": ports[2], 'lladdr':'19:df:73:f6:e3:10'},
            {"device": ports[3], 'lladdr':'70:f6:e2:57:b0:29'}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that FDB static entries added.\n{out}"

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
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:11",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_2": {
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:12",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_3": {
            "ip_source": dev_groups[tg_ports[3]][0]["name"],
            "ip_destination": dev_groups[tg_ports[2]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:13",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_4": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
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

    #verify that address have been forwarded
        for row in stats.Rows:    
            if row ["Traffic Item"] == "bridge_1" and row ["Rx Port"] == tg_ports[1]:
                assert tgen_utils_get_loss == 0.000, f"Verify that traffic from swp1 to swp2 forwarded.\n{out}"
            if row ["Traffic Item"] == "bridge_2" and row ["Rx Port"] == tg_ports[3]:
                assert tgen_utils_get_loss == 0.000, f"Verify that traffic from swp3 to swp4 forwarded.\n{out}"
            if row ["Traffic Item"] == "bridge_3" and row ["Rx Port"] == tg_ports[2]:
                assert tgen_utils_get_loss == 0.000, f"Verify that traffic from swp4 to swp3 forwarded.\n{out}"
            if row ["Traffic Item"] == "bridge_4" and row ["Rx Port"] == tg_ports[0]:
                assert tgen_utils_get_loss == 0.000, f"Verify that traffic from swp2 to swp1 forwarded.\n{out}"
    
    out = await BridgeFdb.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                         parse_output=True)

    devices = out[0][device_host_name]["parsed_output"]
    data = []
    for dev in devices:
         data.append(dev.get("mac", None))
    print(data)

    test_data_in = ["aa:bb:cc:dd:ee:11","aa:bb:cc:dd:ee:12","aa:bb:cc:dd:ee:13","aa:bb:cc:dd:ee:14"]
    for addr in test_data_in :
        assert addr in test_data_in, f"Verify that source macs aa:bb:cc:dd:ee:11,aa:bb:cc:dd:ee:12,aa:bb:cc:dd:ee:13,aa:bb:cc:dd:ee:14 have been learned.\n{out}"

    await tgen_utils_stop_protocols(tgen_dev)


@pytest.mark.asyncio
async def test_bridging_frame_min(testbed):
    """
    Test Name: test_bridging_frame_min
    Test Suite: suite_functional_bridging
    Test Overview: Verifying that Jambo frames of min size are learned and forwarded.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set min jumbo frame MTU size support on ports swp1, swp2, swp3, swp4.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Send traffic from swp1 to swp2.
    9.  Send traffic from swp3 to swp4.
    10. Send traffic from swp4 to swp3.
    11. Send traffic from swp2 to swp1.
    12. Verify that address have been learned and forwarded.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print.error(
            "The testbed does not have enough dent with tgen connections")
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
            {"device": port, "master": "br0", "operstate": "up", "mtu": 1600} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge, bridge entities set to 'UP' state, links enslaved to bridge and min jumbo frame size set to '1600'.\n{out}"
    
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
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:11",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_2": {
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:12",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_3": {
            "ip_source": dev_groups[tg_ports[3]][0]["name"],
            "ip_destination": dev_groups[tg_ports[2]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:13",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_4": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
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
    
    #verify that address have been forwarded
        for row in stats.Rows:    
            if row ["Traffic Item"] == "bridge_1" and row ["Rx Port"] == tg_ports[1]:
                assert tgen_utils_get_loss == 0.000, f"Verify that traffic from swp1 to swp2 forwarded.\n{out}"
            if row ["Traffic Item"] == "bridge_2" and row ["Rx Port"] == tg_ports[3]:
                assert tgen_utils_get_loss == 0.000, f"Verify that traffic from swp3 to swp4 forwarded.\n{out}"
            if row ["Traffic Item"] == "bridge_3" and row ["Rx Port"] == tg_ports[2]:
                assert tgen_utils_get_loss == 0.000, f"Verify that traffic from swp4 to swp3 forwarded.\n{out}"
            if row ["Traffic Item"] == "bridge_4" and row ["Rx Port"] == tg_ports[0]:
                assert tgen_utils_get_loss == 0.000, f"Verify that traffic from swp2 to swp1 forwarded.\n{out}"

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                         parse_output=True)

    devices = out[0][device_host_name]["parsed_output"]
    data = []
    for dev in devices:
         data.append(dev.get("mac", None))
    print(data)

    test_data_in = ["aa:bb:cc:dd:ee:11","aa:bb:cc:dd:ee:12","aa:bb:cc:dd:ee:13","aa:bb:cc:dd:ee:14"]
    for addr in test_data_in :
        assert addr in test_data_in, f"Verify that source macs aa:bb:cc:dd:ee:11,aa:bb:cc:dd:ee:12,aa:bb:cc:dd:ee:13,aa:bb:cc:dd:ee:14 have been learned.\n{out}"

    await tgen_utils_stop_protocols(tgen_dev)


@pytest.mark.asyncio
async def test_bridging_jumbo_frame_learning(testbed):
    """
    Test Name: test_bridging_jumbo_frame_learning
    Test Suite: suite_functional_bridging
    Test Overview: Verify that addresses are learned on bridge with jumbo frames.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set max jumbo frame size support on ports swp1, swp2, swp3, swp4.
    5.  Set bridge br0 admin state UP.
    6.  Set ports swp1, swp2, swp3, swp4 learning ON.
    7.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    8.  Send traffic with max jumbo frame size.
    9.  Verify that address have been learned.
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
            {"device": port, "master": "br0", "operstate": "up", "mtu": 9500} for port in ports]},
            {"device": bridge, "operstate": "up"}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge, bridge entities set to 'UP' state, links enslaved to bridge and max jumbo frame size set to '9500'.\n{out}"
    
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
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:11",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_2": {
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:12",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_3": {
            "ip_source": dev_groups[tg_ports[3]][0]["name"],
            "ip_destination": dev_groups[tg_ports[2]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:13",
            "dstMac": "ff:ff:ff:ff:ff:ff",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "bridge_4": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
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
        assert addr in test_data_in, f"Verify that source macs aa:bb:cc:dd:ee:11,aa:bb:cc:dd:ee:12,aa:bb:cc:dd:ee:13,aa:bb:cc:dd:ee:14 have been learned.\n{out}"

    await tgen_utils_stop_protocols(tgen_dev)
