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
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {"device": bridge, "type": "bridge"}]}])
    err_msg = f"Verify that bridge created.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": bridge, "operstate": "up"}]}])
    err_msg = f"Verify that bridge set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": "br0", "mtu": 9000} for port in ports]}])
    err_msg = f"Verify that bridge min jumbo frame size set to '9000'.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge, bridge entities set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeFdb.add(
        input_data=[{device_host_name: [
            {"device": ports[0], 'lladdr':'cc:f4:ed:5b:15:39'},
            {"device": ports[1], 'lladdr':'fd:64:8a:62:27:8a'},
            {"device": ports[2], 'lladdr':'19:df:73:f6:e3:10'},
            {"device": ports[3], 'lladdr':'70:f6:e2:57:b0:29'}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that FDB static entries added.\n{out}"

    address_map = (
        #swp port, tg port,     tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "2.2.2.2", "2.2.2.1", 24),
        (ports[2], tg_ports[2], "3.3.3.2", "3.3.3.1", 24),
        (ports[3], tg_ports[3], "4.4.4.2", "4.4.4.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)
    
    expected_mac = ["aa:bb:cc:dd:ee:11", "aa:bb:cc:dd:ee:12",
                    "aa:bb:cc:dd:ee:13", "aa:bb:cc:dd:ee:14"]

    streams = {
        f"bridge_{dst + 1}": {
            "ip_source": dev_groups[tg_ports[src]][0]["name"],
            "ip_destination": dev_groups[tg_ports[dst]][0]["name"],
            "srcMac": expected_mac[src],
            "dstMac": expected_mac[dst],
            "type": "raw",
            "protocol": "802.1Q",
        } for src, dst in ((3, 0), (2, 1), (1, 2), (0, 3))
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)
    
    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) != 100.000, f'Failed>Loss percent: {row["Loss %"]}'
        assert tgen_utils_get_loss(row) == 0.000, \
        f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} forwarded.\n{out}"
    
    out = await BridgeFdb.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                         parse_output=True)

    fdb_entries = out[0][device_host_name]["parsed_output"]
    expected_mac = []
    for en in fdb_entries:
        expected_mac.append(en.get("mac", None))
    for addr in expected_mac:
        err_msg = f"Verify that source macs have been learned.\n{out}"
        assert addr in expected_mac, err_msg

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
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {"device": bridge, "type": "bridge"}]}])
    err_msg = f"Verify that bridge created.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": bridge, "operstate": "up"}]}])
    err_msg = f"Verify that bridge set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": "br0", "mtu": 1500} for port in ports]}])
    err_msg = f"Verify that bridge min jumbo frame size set to '1500'.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge, bridge entities set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        #swp port, tg port,     tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "2.2.2.2", "2.2.2.1", 24),
        (ports[2], tg_ports[2], "3.3.3.2", "3.3.3.1", 24),
        (ports[3], tg_ports[3], "4.4.4.2", "4.4.4.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)
    
    expected_mac = ["aa:bb:cc:dd:ee:11", "aa:bb:cc:dd:ee:12",
                    "aa:bb:cc:dd:ee:13", "aa:bb:cc:dd:ee:14"]

    streams = {
        f"bridge_{dst + 1}": {
            "ip_source": dev_groups[tg_ports[src]][0]["name"],
            "ip_destination": dev_groups[tg_ports[dst]][0]["name"],
            "srcMac": expected_mac[src],
            "dstMac": expected_mac[dst],
            "type": "raw",
            "protocol": "802.1Q",
        } for src, dst in ((3, 0), (2, 1), (1, 2), (0, 3))
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)
    
    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert float(row["Tx Frames"]) > 0.000, f'Failed>Ixia should transmit traffic: {row["Tx Frames"]}'

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                         parse_output=True)

    fdb_entries = out[0][device_host_name]["parsed_output"]
    expected_mac = []
    for en in fdb_entries:
        expected_mac.append(en.get("mac", None))
    for addr in expected_mac:
        err_msg = f"Verify that source macs have been learned.\n{out}"
        assert addr in expected_mac, err_msg

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
    8.  Send traffic with jumbo frame size.
    9.  Verify that address have been learned.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 5

    out = await IpLink.add(
        input_data=[{device_host_name: [
            {"device": bridge, "type": "bridge"}]}])
    err_msg = f"Verify that bridge created.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": bridge, "operstate": "up"}]}])
    err_msg = f"Verify that bridge set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": "br0", "mtu": 2000} for port in ports]}])
    err_msg = f"Verify that bridge min jumbo frame size set to '2000'.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": "br0", "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge, bridge entities set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "flood": False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        #swp port, tg port,     tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "2.2.2.2", "2.2.2.1", 24),
        (ports[2], tg_ports[2], "3.3.3.2", "3.3.3.1", 24),
        (ports[3], tg_ports[3], "4.4.4.2", "4.4.4.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)
    
    expected_mac = ["aa:bb:cc:dd:ee:11", "aa:bb:cc:dd:ee:12",
                    "aa:bb:cc:dd:ee:13", "aa:bb:cc:dd:ee:14"]

    streams = {
        f"bridge_{dst + 1}": {
            "ip_source": dev_groups[tg_ports[src]][0]["name"],
            "ip_destination": dev_groups[tg_ports[dst]][0]["name"],
            "srcMac": expected_mac[src],
            "dstMac": expected_mac[dst],
            "type": "raw",
            "protocol": "802.1Q",
        } for src, dst in ((3, 0), (2, 1), (1, 2), (0, 3))
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)
    
     # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert float(row["Tx Frames"]) > 0.000, f'Failed>Ixia should transmit traffic: {row["Tx Frames"]}'

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                         parse_output=True)

    fdb_entries = out[0][device_host_name]["parsed_output"]
    expected_mac = []
    for en in fdb_entries:
        expected_mac.append(en.get("mac", None))
    for addr in expected_mac:
        err_msg = f"Verify that source macs have been learned.\n{out}"
        assert addr in expected_mac, err_msg

    await tgen_utils_stop_protocols(tgen_dev)
