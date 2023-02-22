import re
import pytest
import asyncio

from random import randrange
from dent_os_testbed.lib.ip.ip_link import IpLink

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
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")
]

async def test_bridging_bum_traffic_bridge_without_rif(testbed):
    """
    Test Name: test_bridging_bum_traffic_bridge_without_rif
    Test Suite: suite_functional_bridging
    Test Overview: Verify forwarding/drop/trap of different broadcast, unknown-unicast
                   and multicast traffic L2, IPv4 packet types within the same bridge domain.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1. Init bridge entity br0.
    2. Set ports swp1, swp2, swp3, swp4 master br0.
    3. Set entities swp1, swp2, swp3, swp4 UP state.
    4. Set bridge br0 admin state UP.
    5. Get self MAC address on ingress port swp1.
    6. Start tcpdump capture on DUT ingress port.
    7. Send different types of packets from source TG.
    8. Analyze counters: a) TX vs RX counters according to expected values;
                         b) Trapped packets to CPU.
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
        input_data=[{device_host_name: [
            {"device": bridge, "type": "bridge"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge created.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": bridge, "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": bridge, "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

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
        #     # "root_id": "8000.34:ef:b6:ec:26:c3",
        #     # "protocolVId": "00",
        #     "srcMac": srcMac,
        #     "dstMac": "01:80:C2:00:00:00",
        #     "frameSize": 96,
        #     "protocol": "ip",
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
        #      "frameSize": 130,
        #     "protocol": "0x8809",
        #     "type" :"raw"
        # },
        "IPv4ToMe": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "ARPRequestBC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": "FF:FF:FF:FF:FF:FF",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "ARPReply": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
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
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": "FF:FF:FF:FF:FF:FF",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPV4_SSH": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "22",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPV4_Telnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "23",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "Default_IPv4": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "tcp",
            "srcPort": str(randrange(0xffff + 1)),
            "dstPort": "23",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_ICMPRequest": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "ipproto": "icmpv1",
            "frameSize": 96,
            "protocol": "ip",
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
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_ReservedMC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": {"type": "increment",
                       "start": srcMac,
                       "step": "00:00:00:00:10:00",
                       "count": 32},
            "dstMac": "01:00:5E:00:00:45",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_AllSysInSubnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:01",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_AllRoutersInSubnet": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:02",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_OSPFIGP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": {"type": "increment",
                       "start": srcMac,
                       "step": "00:00:00:00:10:00",
                       "count": 2},
            "dstMac": "01:00:5E:00:00:05",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_RIP2": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:09",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_EIGRP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:0A",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_DHCPServerRelay": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:0C",
            "ipproto": "udp",
            "srcPort": "68",
            "dstPort": "67",
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_VRRP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:12",
            # "packet.ipv4.protocol": 112,
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        },
        "IPv4_IGMP" : {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "frameSize": 96,
            "srcMac": srcMac,
            "dstMac": "01:00:5E:00:00:16",
            "protocol": "ip",
            "type" :"raw"
        },
        "IPV4_BGP": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcIp": "1.1.1.2",
            "dstIp": "1.1.1.3",
            "ipproto": "tcp",
            "srcPort": "179",
            "dstPort": "179",
            "srcMac": srcMac,
            "dstMac": self_mac,
            "frameSize": 96,
            "protocol": "ip",
            "type" :"raw"
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    tcpdump = asyncio.create_task(tb_device_tcpdump(dent_dev, "swp1", "-n", count_only=False, timeout=5, dump=True))

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    expected_loss = {
        "Bridged_UnknownL2UC": 0,
        # "STP_BPDU": 100,
        "BridgedLLDP": 100,
        # "LACPDU": 100,
        "IPv4ToMe": 100,
        "ARPRequestBC": 0,
        "ARPReply": 100,
        "IPv4_Broadcast": 0,
        "IPV4_SSH": 100,
        "IPV4_Telnet": 100,
        "Default_IPv4": 100,
        "IPv4_ICMPRequest": 100,
        "IPv4_DCHP_BC": 0,
        "IPv4_ReservedMC" :0,
        "IPv4_AllSysInSubnet": 0,
        "IPv4_AllRoutersInSubnet": 0,
        "IPv4_OSPFIGP" : 0,
        "IPv4_RIP2": 0,
        "IPv4_EIGRP": 0,
        "IPv4_DHCPServerRelay": 0,
        "IPv4_VRRP": 0,
        "IPv4_IGMP": 0,
        "IPV4_BGP": 100,
    }
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == expected_loss[row["Traffic Item"]], \
            f"Verify that traffic from swp1 to swp2 forwarded/not forwarded in accordance.\n"

    await tcpdump
    print(f"TCPDUMP: packets={tcpdump.result()}")
    data = tcpdump.result()

    count_of_packets = re.findall(r"(\d+) packets (captured|received|dropped)", data)
    for count, type in count_of_packets:
        if type == "captured" or type == "received":
            assert int(count) > 0, f"Verify that packets are captured and received.\n"
        if type == "dropped":
            assert int(count) == 0, f"Verify that packets are dropped by kernel.\n"
