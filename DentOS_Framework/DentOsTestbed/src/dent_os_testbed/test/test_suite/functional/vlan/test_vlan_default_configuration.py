import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tgen_utils import (tgen_utils_get_dent_devices_with_tgen,
                                                         tgen_utils_setup_streams, tgen_utils_start_traffic,
                                                         tgen_utils_stop_traffic, tgen_utils_get_traffic_stats,
                                                         tgen_utils_get_loss, tgen_utils_dev_groups_from_config,
                                                         tgen_utils_traffic_generator_connect, )
from dent_os_testbed.utils.test_utils.br_utils import get_traffic_port_vlan_mapping

pytestmark = [pytest.mark.suite_functional_vlan,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]

packet_vids = ['X', 1, 2]  # VLAN tag number contained in the transmitted packet
port_map = ({"port": 0, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
            {"port": 1, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
            {"port": 2, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]},
            {"port": 3, "settings": [{"vlan": 1, "untagged": True, "pvid": True}]})


@pytest.mark.parametrize("traffic_type", ["broadcast", "multicast", "unicast", "unknown_unicast"])
async def test_vlan_default_configuration_with_(testbed, traffic_type):
    """
    Test Name: VLAN default configuration
    Test Suite: suite_functional_vlan
    Test Overview: Test packet forwarding with VLAN default configuration
    Test Procedure:
    1. Initiate test params.
    2. Map receiving and non receiving dut_ports.
    3. Setup packet stream(s) for the packet:
    4. Send traffic to rx_ports
    5. Verify traffic on rx ports
    """

    # 1. Initiate test params.
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    device = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[device][0]
    dut_ports = tgen_dev.links_dict[device][1]

    out = await IpLink.add(input_data=[{device: [{
        "device": "br0",
        "type": "bridge",
        "vlan_filtering": 1
        }]
    }])
    assert out[0][device]["rc"] == 0, f"Failed creating bridge."

    await IpLink.set(input_data=[{device: [{"device": "br0", "operstate": "up"}]}])
    assert out[0][device]["rc"] == 0, f"Failed setting bridge to state UP."

    out = await IpLink.set(input_data=[{device: [{
        "device": port,
        "operstate": "up",
        "master": "br0"
    } for port in dut_ports]}])
    assert out[0][device]["rc"] == 0, f"Failed setting link to state UP."

    # 2.Map receiving and non receiving dut_ports.
    dev_groups = tgen_utils_dev_groups_from_config([
        {"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24, },
        {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24, },
        {"ixp": tg_ports[2], "ip": "100.1.1.4", "gw": "100.1.1.6", "plen": 24, },
        {"ixp": tg_ports[3], "ip": "100.1.1.5", "gw": "100.1.1.6", "plen": 24, }])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    tx_ports = dev_groups[tg_ports[0]][0]["name"]
    rx_ports = [dev_groups[tg_ports[1]][0]["name"],
                dev_groups[tg_ports[2]][0]["name"],
                dev_groups[tg_ports[3]][0]["name"]]
    src_mac = "02:00:00:00:00:01"
    # 3. Setup packet stream(s).
    if traffic_type == "broadcast":
        streams = {f"Traffic with VLAN ID: {vlan}": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "src_mac": src_mac,
            "dst_mac": "ff:ff:ff:ff:ff:ff",
            "vlanID": vlan
        } for vlan in packet_vids if vlan != "X"}

        streams.update({"Untagged traffic": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "src_mac": "02:00:00:00:00:01",
            "dst_mac": "ff:ff:ff:ff:ff:ff"
        }})
    elif traffic_type == "multicast":
        streams = {f"Traffic with VLAN ID: {vlan}": {
            "type": "raw",
            "rate": 50,
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "src_mac": src_mac,
            "dst_mac": "01:80:C2:00:00:00",
            "vlanID": vlan
        } for vlan in packet_vids if vlan != "X"}

        streams.update({"Untagged traffic": {
            "type": "raw",
            "rate": 50,
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "src_mac": src_mac,
            "dst_mac": "01:80:C2:00:00:00"
        }})
    elif traffic_type == "unknown_unicast":
        streams = {f"{tg_ports[0]} -> with VLAN: {vlan}": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "srcMac": src_mac,
            "dstMac": "02:00:00:00:00:02",
            "vlanID": vlan
        } for vlan in packet_vids if vlan != "X"}

        # Untagged stream
        streams.update({"Untagged stream": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": tx_ports,
            "ip_destination": rx_ports,
            "srcMac": src_mac,
            "dstMac": "02:00:00:00:00:02",
        }})
    else:
        dst_mac = "02:00:00:00:00:04"
        streams = {f"{tg_ports[0]} -> {vlan}": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source":  dev_groups[tg_ports[0]][0]["name"],
            "ip_destination":  [dev_groups[tg_ports[3]][0]["name"]],
            "src_mac": src_mac,
            "dst_mac": dst_mac,
            "vlanID": vlan
        } for vlan in packet_vids if vlan != "X"}

        streams.update({f"{tg_ports[0]} -> X": {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source":  dev_groups[tg_ports[0]][0]["name"],
            "ip_destination":  [dev_groups[tg_ports[3]][0]["name"]],
            "src_mac": src_mac,
            "dst_mac": dst_mac
        }})

        streams.update({f'{tg_ports[3]} -> {tg_ports[0]}': {
            "type": "raw",
            "protocol": "802.1Q",
            "ip_source": dev_groups[tg_ports[3]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "src_mac": dst_mac,
            "dst_mac": src_mac,
            "vlanID": 1
        }})

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 4. Send traffic to rx_ports.
    if traffic_type == "unicast":
        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(1)
        await tgen_utils_stop_traffic(tgen_dev)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(1)
    await tgen_utils_stop_traffic(tgen_dev)

    # 6. Verify traffic.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    ti_to_rx_port_map = get_traffic_port_vlan_mapping(streams, port_map, tg_ports)
    for row in stats.Rows:
        if row["Rx Port"] in ti_to_rx_port_map[row["Traffic Item"]]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f'No traffic for traffic item : {row["Traffic Item"]} on port {row["Rx Port"]}'
        else:
            assert tgen_utils_get_loss(row) == 100.000, \
                f'Traffic leak for traffic item: {row["Traffic Item"]} on port {row["Rx Port"]}'
