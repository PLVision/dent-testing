import itertools
import asyncio
import pytest
import random
import pdb

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_stop_protocols,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_get_swp_info,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

pytestmark = pytest.mark.suite_functional_ipv4


def get_random_ip():
    ip = [random.randint(1, 253) for _ in range(4)]
    peer = ip[:-1] + [ip[-1] + 1]
    plen = random.randint(1, 31)
    return ".".join(map(str, ip)), ".".join(map(str, peer)), plen


@pytest.mark.asyncio
async def test_ipv4_random_routing(testbed):
    """
    Test Name: test_ipv4_random_routing
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 random routing
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Enable IPv4 forwarding
    4. Configure random IP addrs on all interfaces
    5. Generate traffic and verify reception
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [{"device": port, "operstate": "up"}
                                               for port in ports]}])
    assert out[0][dent]["rc"] == 0

    # 3. Enable IPv4 forwarding
    rc, out = await dent_dev.run_cmd(f"sysctl -n net.ipv4.ip_forward=1")
    assert rc == 0

    # 4. Configure random IP addrs on all interfaces
    address_map = (
        # swp port, tg port,    swp ip, tg ip, plen
        (ports[0], tg_ports[0], *get_random_ip()),
        (ports[1], tg_ports[1], *get_random_ip()),
        (ports[2], tg_ports[2], *get_random_ip()),
        (ports[3], tg_ports[3], *get_random_ip()),
    )

    out = await IpAddress.flush(input_data=[{dent: [
        {"dev": port} for port in ports
    ]}])
    assert out[0][dent]["rc"] == 0

    out = await IpAddress.add(input_data=[{dent: [
        {"dev": port, "prefix": f"{ip}/{plen}"}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]["rc"] == 0

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # 5. Generate traffic and verify reception
    streams = {
        f"{tg1} <-> {tg2}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg1][0]["name"],
            "ip_destination": dev_groups[tg2][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "bi_directional": True,
        } for tg1, tg2 in itertools.combinations(tg_ports, 2)
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000

    await tgen_utils_stop_protocols(tgen_dev)


@pytest.mark.asyncio
async def test_ipv4_nexthop_route(testbed):
    """
    Test Name: test_ipv4_nexthop_route
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 nexthop routing
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Enabling IPv4 forwarding
    4. Configure IP addrs
    5. Add static arp entries
    6. Add routes nexthopes
    7. Transmit traffic for routes and verify reception
    """
    # 1. Init interfaces
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [{"device": port, "operstate": "up"}
                                               for port in ports]}])
    assert out[0][dent]["rc"] == 0

    # 3. Enable IPv4 forwarding
    rc, out = await dent_dev.run_cmd(f"sysctl -n net.ipv4.ip_forward=1")
    assert rc == 0

    # 4. Configure IP addrs
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "1.1.1.1", "1.1.1.2", 24),
        (ports[1], tg_ports[1], "2.2.2.1", "2.2.2.2", 24),
    )

    out = await IpAddress.flush(input_data=[{dent: [
        {"dev": port} for port in ports
    ]}])
    assert out[0][dent]["rc"] == 0

    out = await IpAddress.add(input_data=[{dent: [
        {"dev": port, "prefix": f"{ip}/{plen}"}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]["rc"] == 0

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports[:2], ports[:2], dev_groups)

    # 5. Add static arp entries
    out = await IpNeighbor.add(input_data=[{dent: [
        {"dev": ports[0], "address": "1.1.1.5", "lladdr": "aa:bb:cc:dd:ee:01"},
        {"dev": ports[1], "address": "2.2.2.5", "lladdr": "aa:bb:cc:dd:ee:02"},
    ]}])
    assert out[0][dent]["rc"] == 0

    # 6. Add routes nexthopes
    out = await IpRoute.add(input_data=[{dent: [
        {"dst": "48.0.0.0/24", "nexthop": [{"via": "1.1.1.5"}]},
        {"dst": "16.0.0.0/24", "nexthop": [{"via": "2.2.2.5"}]},
    ]}])
    assert out[0][dent]["rc"] == 0

    # 7. Transmit traffic for routes and verify reception
    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, ports[0], swp_info)
    mac_port0 = swp_info["mac"]

    await tgen_utils_get_swp_info(dent_dev, ports[1], swp_info)
    mac_port1 = swp_info["mac"]

    streams = {
        f"{tg_ports[0]} -> {tg_ports[1]}": {
            "type": "raw",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "srcMac": "aa:bb:cc:dd:ee:01",
            "dstMac": mac_port0,
            "srcIp": "1.1.1.2",
            "dstIp": "16.0.0.0",
        },
        f"{tg_ports[1]} -> {tg_ports[0]}": {
            "type": "raw",
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "srcMac": "aa:bb:cc:dd:ee:02",
            "dstMac": mac_port1,
            "srcIp": "2.2.2.2",
            "dstIp": "48.0.0.0",
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000

    await tgen_utils_stop_protocols(tgen_dev)


@pytest.mark.asyncio
async def test_ipv4_route_btw_vlan_devices(testbed):
    """
    Test Name: test_ipv4_route_btw_vlan_devices
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 route between vlan devices
    Test Procedure:
    1. Create a bridge entity
    2. Enslave ports to bridge and create VLAN-devices
    3. Set link up on all participant ports and VLAN-devices and add bridges to VLAN of the VLAN-devices
    4. Configure ip address on VLAN-devices and then add ports to VLANs
    5. Verify offload flag appear in VLAN-devices default routes
    6. Prepare streams from one VLAN-device`s neighbor to the other
    7. Transmit Traffic
    8. Verify traffic is forwarded to both VLAN-devices` neighbors
    9. Remove IP address from VLAN-devices and re-configure; Send ARPs and transmit again
    10. Verify offload flag appear in VLAN-devices default routes
    11. Verify traffic is forwarded to both VLAN-devices` neighbors
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]
    traffic_duration = 10
    bridge = "br0"
    vlan10 = f"{bridge}.10"
    vlan20 = f"{bridge}.20"

    address_map = (
        # swp port, vlan iface, tg port, swp ip,   tg ip,    plen, vid
        (ports[0], vlan10, tg_ports[0], "1.1.1.1", "1.1.1.2", 24,  10),
        (ports[1], vlan20, tg_ports[1], "2.2.2.1", "2.2.2.2", 24,  20),
    )

    # Enable IPv4 forwarding
    rc, out = await dent_dev.run_cmd(f"sysctl -n net.ipv4.ip_forward=1")
    assert rc == 0

    # 1. Create a bridge entity
    out = await IpLink.delete(input_data=[{dent: [
        {"device": dev} for dev in (bridge, vlan10, vlan20)
    ]}])

    out = await IpLink.add(input_data=[{dent: [
        {"device": bridge, "type": "bridge", "vlan_filtering": 1, "vlan_default_pvid": 0},
    ]}])
    assert out[0][dent]["rc"] == 0

    # 2. Enslave ports to bridge
    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "master": bridge} for port in ports[:2]
    ]}])
    assert out[0][dent]["rc"] == 0

    # Create VLAN-devices
    out = await IpLink.add(input_data=[{dent: [
        {"link": bridge, "name": vlan, "type": f"vlan id {id}"}
        for _, vlan, _, _, _, _, id in address_map
    ]}])
    assert out[0][dent]["rc"] == 0

    # 3. Set link up on all participant ports and VLAN-devices
    out = await IpLink.set(input_data=[{dent: [
        {"device": dev, "operstate": "up"}
        for dev in ports[:2] + [bridge, vlan10, vlan20]
    ]}])
    assert out[0][dent]["rc"] == 0

    # Add bridges to VLAN of the VLAN-devices
    out = await BridgeVlan.add(input_data=[{dent: [
        {"device": bridge, "vid": address_map[0][6], "self": True},
        {"device": bridge, "vid": address_map[1][6], "self": True},
    ]}])
    assert out[0][dent]["rc"] == 0

    # 4. Configure ip address on VLAN-devices and add ports to VLANs
    out = await IpAddress.flush(input_data=[{dent: [
        {"dev": port} for port in ports
    ]}])
    assert out[0][dent]["rc"] == 0

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": tg_port, "ip": ip, "gw": gw, "plen": plen, "vlan": vid}
        for _, _, tg_port, gw, ip, plen, vid in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports[:2], ports[:2], dev_groups)

    out = await BridgeVlan.add(input_data=[{dent: [
        {"device": port, "vid": vid}
        for port, _, _, _, _, _, vid in address_map
    ]}])
    assert out[0][dent]["rc"] == 0

    out = await IpAddress.add(input_data=[{dent: [
        {"dev": vlan, "prefix": f"{ip}/{plen}"}
        for _, vlan, _, ip, _, plen, _ in address_map
    ]}])
    assert out[0][dent]["rc"] == 0

    # 5. Verify offload flag appear in VLAN-devices default routes
    out = await IpRoute.show(input_data=[{dent: [
        {"cmd_options": "-j"}
    ]}], parse_output=True)
    assert out[0][dent]["rc"] == 0

    for route in out[0][dent]["parsed_output"]:
        if route.get("dev", None) in (vlan10, vlan20):
            assert "offload" in route["flags"]

    # 6. Prepare streams from one VLAN-device`s neighbor to the other
    streams = {
        f"{tg_ports[0]} -> {tg_ports[1]}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
        },
        f"{tg_ports[1]} -> {tg_ports[0]}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    # 7. Transmit Traffic
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Verify traffic is forwarded to both VLAN-devices` neighbors
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000

    # 9. Remove IP address from VLAN-devices
    out = await IpAddress.flush(input_data=[{dent: [
        {"dev": vlan10},
        {"dev": vlan20},
    ]}])
    assert out[0][dent]["rc"] == 0

    # Re-configure
    out = await IpAddress.add(input_data=[{dent: [
        {"dev": vlan, "prefix": f"{ip}/{plen}"}
        for _, vlan, _, ip, _, plen, _ in address_map
    ]}])
    assert out[0][dent]["rc"] == 0

    # Transmit again
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 10. Verify offload flag appear in VLAN-devices default routes
    out = await IpRoute.show(input_data=[{dent: [
        {"cmd_options": "-j"}
    ]}], parse_output=True)
    assert out[0][dent]["rc"] == 0

    for route in out[0][dent]["parsed_output"]:
        if route.get("dev", None) in (vlan10, vlan20):
            assert "offload" in route["flags"]

    # 11. Verify traffic is forwarded to both VLAN-devices` neighbors
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000

    await tgen_utils_stop_protocols(tgen_dev)
