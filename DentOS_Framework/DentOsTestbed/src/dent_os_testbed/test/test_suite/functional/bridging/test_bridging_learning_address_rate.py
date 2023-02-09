import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")
]

async def test_bridging_learning_address_rate(testbed):
    """
    Test Name: test_bridging_learning_address_rate
    Test Suite: suite_functional_bridging
    Test Overview: Verify the bridge entries and make sure no packets were flooded into port 3.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood ON.
    7.  Send traffic to swp1 to learn source increment address 
        00:00:00:00:00:35 with step '00:00:00:00:10:00' and count 1000.
    8.  Send traffic to swp2 with destination increment address 
        00:00:00:00:00:35 with step '00:00:00:00:10:00' and count 1000.
    9.  Verify that there was not flooding to swp3.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 3)
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
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge created.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": bridge, "operstate": "up"}]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify that bridge set to 'UP' state.\n{out}"

    out = await IpLink.set(
        input_data=[{device_host_name: [
            {"device": port, "master": bridge, "operstate": "up"} for port in ports]}])
    err_msg = f"Verify that bridge, bridge entities set to 'UP' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True, "True": True} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'ON' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        #swp port, tg port,     tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24),
        (ports[2], tg_ports[2], "1.1.1.4", "1.1.1.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "streamA": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "srcMac": {"type": "increment",
                   "start": "00:00:00:00:00:35",
                   "step": "00:00:00:00:10:00",
                   "count": 1000},
            "dstMac": "aa:bb:cc:dd:ee:11",
            "type": "raw",
            "protocol": "802.1Q",
        },
        "streamB": {
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": "aa:bb:cc:dd:ee:12",
            "dstMac": {"type": "increment",
                   "start": "00:00:00:00:00:35",
                   "step": "00:00:00:00:10:00",
                   "count": 1000},
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
        if row["Traffic Item"] == "streamA" and row["Rx Port"] == tg_ports[0]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f"Verify that traffic from swp2 to swp1 forwarded.\n"
        if row["Traffic Item"] == "streamB" and row["Rx Port"] == tg_ports[1]:
            assert tgen_utils_get_loss(row) == 0.000, \
                f"Verify that traffic from swp3 to swp2 forwarded.\n"
        if row["Traffic Item"] == "streamA" and row["Rx Port"] == tg_ports[2]:
            assert tgen_utils_get_loss(row) == 100.000, \
                f"Verify that traffic to swp3 not forwarded.\n"
        if row["Traffic Item"] == "streamB" and row["Rx Port"] == tg_ports[2]:
            assert tgen_utils_get_loss(row) == 100.000, \
                f"Verify that traffic to swp3 not forwarded.\n"
