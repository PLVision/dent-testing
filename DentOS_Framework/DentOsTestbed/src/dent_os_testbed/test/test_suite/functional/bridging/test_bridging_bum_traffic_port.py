import re
import pytest
import asyncio

from random import randrange
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

from dent_os_testbed.utils.test_utils.tb_utils import (
    tb_device_tcpdump
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen", "cleanup_ip_addrs")
]

async def test_bridging_bum_traffic_port_with_rif(testbed):
    """
    Test Name: test_bridging_bum_traffic_port_with_rif
    Test Suite: suite_functional_bridging
    Test Overview: Verify forwarding/drop/trap of different broadcast, unknown-unicast
                   and multicast traffic L2, IPv4 packet types.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init ports.
    2. Configure IP addresses on ports.
    3. Set entities swp1, swp2, swp3, swp4 UP state.
    4. Get self MAC address on ingress port swp1.
    5. Start tcpdump capture on DUT ingress port.
    6. Send different types of packets from source TG.
    7. Analyze counters: a) TX vs RX counters according to expected values;
                         b) Trapped packets to CPU.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10

    out = await IpAddress.add(input_data=[{device_host_name: [
        {"dev": ports[0], "prefix": "100.1.1.253/24"},
        {"dev": ports[1], "prefix": "101.1.1.253/24"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Failed to add IP address to ports.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "operstate": "up"} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that entities set to 'UP' state.\n{out}"

    out = await IpLink.show(input_data=[{device_host_name: [{"device": ports[0], "cmd_options": "-j"}]}],
                            parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, f"Failed to display device attributes.\n{out}"

    dev_attributes = out[0][device_host_name]["parsed_output"]
    self_mac = dev_attributes[0]["address"]
    srcMac = "00:00:AA:00:00:01"

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "Bridged_UnknownL2UC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": srcMac,
            "dstMac": "00:00:BB:11:22:33",
            "frameSize": 96,
            "protocol": "0x6666",
            "type" :"raw",
        },
        # # TODO: FIX
        # "STP_BPDU": {
        #     "ip_source": dev_groups[tg_ports[0]][0]["name"],
        #     "ip_destination": dev_groups[tg_ports[1]][0]["name"],
        #     "root_id": "8000.34:ef:b6:ec:26:c3",
        #     #"protocolVId": "00",
        #     "srcMac": srcMac,
        #     "dstMac": "01:80:C2:00:00:00",
        #     "frameSize": 96,
        #     "protocol": "0x0800",
        #     "type" :"raw"
        # },
        "BridgedLLDP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": srcMac,
            "dstMac": "01:80:c2:00:00:0e",
            "frameSize": 96,
            "protocol": "0x88cc",
            "type" :"raw"
        },
        #  # TODO: FIX
        # "LACPDU": {
        #     "ip_source": dev_groups[tg_ports[0]][0]["name"],
        #     "ip_destination": dev_groups[tg_ports[1]][0]["name"],
        #     "srcMac": srcMac,
        #     "dstMac": "01:80:c2:00:00:02",
        #     # "partnerMac": Randomize().Mac(),
        #     "frameSize": 130,
        #     "protocol": "0x8809",
        #     "type" :"raw"
        # },
        "IPv4ToMe": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "ARP_Request_BC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": "FF:FF:FF:FF:FF:FF",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "ARP_Reply": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "frameSize": 96,
            "protocol": "0x0000",
            "type" :"raw"
        },
        "IPv4_Broadcast": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.255",
            "srcMac": srcMac,
            "dstMac": "FF:FF:FF:FF:FF:FF",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPV4_SSH": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "22",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPV4_Telnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "23",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "Default_IPv4": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "192.168.1.1",
            "dstIp": "192.168.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "23",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_ICMP_Request": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "icmpv1",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_DCHP_BC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "0.0.0.0",
            "dstIp": "255.255.255.255",
            "srcMac": srcMac,
            "dstMac": "FF:FF:FF:FF:FF:FF",
            "frameSize": 346,
            "ipproto": "udp",
            "srcPort": "67",
            "dstPort": "68",
            "frameSize": 346,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_Reserved_MC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.69",
            "srcMac": {"type": "increment",
                       "start": srcMac,
                       "step": "00:00:00:00:10:00",
                       "count": 32},
            "dstMac": "01:00:5E:00:00:45",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_All_Systems_on_this_Subnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.1",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:01",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_All_Routers_on_this_Subnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.2",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:02",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_OSPFIGP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.5",
            "srcMac": {"type": "increment",
                       "start": srcMac,
                       "step": "00:00:00:00:10:00",
                       "count": 2},
            "dstMac": "01:00:5E:00:00:05",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_RIP2_Routers": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.9",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:09",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_EIGRP_Routers": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.10",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:0A",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_DHCP_Server/Relay_Agent": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.12",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:0C",
            "ipproto": "udp",
            "srcPort": "68",
            "dstPort": "67",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_VRRP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.18",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:12",
            # "packet.ipv4.protocol": 112,
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_IGMP" : {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.22",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:16",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPV4_BGP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "ipproto": "tcp",
            "srcPort": "179",
            "dstPort": "179",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    tcpdump = asyncio.create_task(tb_device_tcpdump(dent_dev, "swp1", "-n", count_only=False, timeout=5, dump=True))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"

    await tcpdump
    print(f"TCPDUMP: packets={tcpdump.result()}")
    data = tcpdump.result()

    count_of_packets = re.findall(r"(\d+) packets (captured|received|dropped)", data)
    for count, type in count_of_packets:
        if type == "captured" or type == "received":
            assert int(count) > 0, f"Verify that packets are captured and received.\n"
        if type == "dropped":
            assert int(count) == 0, f"Verify that packets are dropped by kernel.\n"


async def test_bridging_bum_traffic_port_without_rif(testbed):
    """
    Test Name: test_bridging_bum_traffic_port_without_rif
    Test Suite: suite_functional_bridging
    Test Overview: Verify forwarding/drop/trap of different broadcast, unknown-unicast
                   and multicast traffic L2, IPv4 packet types.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init ports.
    2. Set entities swp1, swp2, swp3, swp4 UP state.
    3. Get self MAC address on ingress port swp1.
    4. Start tcpdump capture on DUT ingress port.
    5. Send different types of packets from source TG.
    6. Analyze counters: a) TX vs RX counters according to expected values;
                         b) Trapped packets to CPU.
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1]
    traffic_duration = 10

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "operstate": "up"} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that entities set to 'UP' state.\n{out}"

    out = await IpLink.show(input_data=[{device_host_name: [{"device": ports[0], "cmd_options": "-j"}]}],
                            parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, f"Failed to display device attributes.\n{out}"

    dev_attributes = out[0][device_host_name]["parsed_output"]
    self_mac = dev_attributes[0]["address"]
    srcMac = "00:00:AA:00:00:01"

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24)
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "Bridged_UnknownL2UC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": srcMac,
            "dstMac": "00:00:BB:11:22:33",
            "frameSize": 96,
            "protocol": "0x6666",
            "type" :"raw",
        },
        # # TODO: FIX
        # "STP_BPDU": {
        #     "ip_source": dev_groups[tg_ports[0]][0]["name"],
        #     "ip_destination": dev_groups[tg_ports[1]][0]["name"],
        #     "root_id": "8000.34:ef:b6:ec:26:c3",
        #     #"protocolVId": "00",
        #     "srcMac": srcMac,
        #     "dstMac": "01:80:C2:00:00:00",
        #     "frameSize": 96,
        #     "protocol": "0x0800",
        #     "type" :"raw"
        # },
        "BridgedLLDP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": srcMac,
            "dstMac": "01:80:c2:00:00:0e",
            "frameSize": 96,
            "protocol": "0x88cc",
            "type" :"raw"
        },
        #  # TODO: FIX
        # "LACPDU": {
        #     "ip_source": dev_groups[tg_ports[0]][0]["name"],
        #     "ip_destination": dev_groups[tg_ports[1]][0]["name"],
        #     "srcMac": srcMac,
        #     "dstMac": "01:80:c2:00:00:02",
        #     # "partnerMac": Randomize().Mac(),
        #     "frameSize": 130,
        #     "protocol": "0x8809",
        #     "type" :"raw"
        # },
        "IPv4ToMe": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "ARP_Request_BC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": "FF:FF:FF:FF:FF:FF",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "ARP_Reply": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "frameSize": 96,
            "protocol": "0x0000",
            "type" :"raw"
        },
        "IPv4_Broadcast": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.255",
            "srcMac": srcMac,
            "dstMac": "FF:FF:FF:FF:FF:FF",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPV4_SSH": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "22",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPV4_Telnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "23",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "Default_IPv4": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "192.168.1.1",
            "dstIp": "192.168.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "23",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_ICMP_Request": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "icmpv1",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_DCHP_BC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "0.0.0.0",
            "dstIp": "255.255.255.255",
            "srcMac": srcMac,
            "dstMac": "FF:FF:FF:FF:FF:FF",
            "frameSize": 346,
            "ipproto": "udp",
            "srcPort": "67",
            "dstPort": "68",
            "frameSize": 346,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_Reserved_MC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.69",
            "srcMac": {"type": "increment",
                       "start": srcMac,
                       "step": "00:00:00:00:10:00",
                       "count": 32},
            "dstMac": "01:00:5E:00:00:45",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_All_Systems_on_this_Subnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.1",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:01",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_All_Routers_on_this_Subnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.2",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:02",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_OSPFIGP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.5",
            "srcMac": {"type": "increment",
                       "start": srcMac,
                       "step": "00:00:00:00:10:00",
                       "count": 2},
            "dstMac": "01:00:5E:00:00:05",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_RIP2_Routers": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.9",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:09",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_EIGRP_Routers": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.10",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:0A",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_DHCP_Server/Relay_Agent": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.12",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:0C",
            "ipproto": "udp",
            "srcPort": "68",
            "dstPort": "67",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_VRRP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.18",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:12",
            # "packet.ipv4.protocol": 112,
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPv4_IGMP" : {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "224.0.0.22",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:16",
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        },
        "IPV4_BGP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "100.1.1.253",
            "ipproto": "tcp",
            "srcPort": "179",
            "dstPort": "179",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "frameSize": 96,
            "protocol": "0x0800",
            "type" :"raw"
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    tcpdump = asyncio.create_task(tb_device_tcpdump(dent_dev, "swp1", "-n", count_only=False, timeout=5, dump=True))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} not forwarded.\n{out}"

    await tcpdump
    print(f"TCPDUMP: packets={tcpdump.result()}")
    data = tcpdump.result()

    count_of_packets = re.findall(r"(\d+) packets (captured|received|dropped)", data)
    for count, type in count_of_packets:
        if type == "captured" or type == "received":
            assert int(count) > 0, f"Verify that packets are captured and received.\n"
        if type == "dropped":
            assert int(count) == 0, f"Verify that packets are dropped by kernel.\n"
