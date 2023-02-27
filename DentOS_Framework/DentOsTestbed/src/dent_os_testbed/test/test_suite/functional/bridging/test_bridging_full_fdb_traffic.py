import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.bridge.bridge_fdb import BridgeFdb
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_clear_traffic_items,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")
]

async def test_bridging_full_fdb_traffic(testbed):
    """
    Test Name: test_bridging_full_fdb_traffic
    Test Suite: suite_functional_bridging
    Test Overview: Verify bridge mac table size and traffic verification.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Send traffic to swp1 to learn source increment address
        00:00:00:00:00:35 with step '00:00:00:00:10:00' and count 4000.
    7.  Verify amount.
    8.  Verify that address 00:00:00:00:00:35 and 00:00:00:08:f0:35
        have been learned for swp1 with traffic.
    9.  Delete traffic item streamA.
    10. Send traffic to swp2 to learn source increment address
        00:00:00:00:00:35 with step '00:00:00:00:10:00' and count 4000.
    11. Verify amount.
    12. Verify that address 00:00:00:00:00:35 and 00:00:00:08:f0:35
        have been learned for swp2 with traffic.
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
    traffic_duration = 15
    ixia_vhost_mac_count = 2

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

    out = await BridgeLink.set(
        input_data=[{device_host_name: [
            {"device": port, "learning": True} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24),
    )

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, ip, gw, plen in address_map
    )

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        "streamA": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": {"type": "increment",
                       "start": "00:00:00:00:00:35",
                       "step": "00:00:00:00:10:00",
                       "count": 4000},
            "dstMac": "aa:bb:cc:dd:ee:11",
            "type": "raw",
            "protocol": "802.1Q",
            "rate": "1000",
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f"Expected loss: 0%, actual: {loss}%"

    rc, out = await dent_dev.run_cmd("bridge fdb show br br0   |  grep 'extern_learn.*offload'  |  wc -l")
    assert rc == 0, f"Failed to grep 'extern_learn.*offload'.\n"

    amount = int(out) - ixia_vhost_mac_count
    err_msg = f"Expected count of extern_learn offload entities: 4000, Actual count: {amount}"
    assert amount  == 4000, err_msg

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    list_macs = ["00:00:00:00:00:35", "00:00:00:08:f0:35"]
    for mac in list_macs:
        err_msg = f"Expected MACs are not found in FDB, but found MACs:{out}\n"
        assert mac in learned_macs, err_msg

    await tgen_utils_clear_traffic_items(tgen_dev)

    streams = {
        "streamB": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "srcMac": {"type": "increment",
                       "start": "00:00:00:00:00:35",
                       "step": "00:00:00:00:10:00",
                       "count": 4000},
            "dstMac": "aa:bb:cc:dd:ee:12",
            "type": "raw",
            "protocol": "802.1Q",
            "rate": "1000",
        }
    }

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f"Expected loss: 0%, actual: {loss}%"

    rc, out = await dent_dev.run_cmd("bridge fdb show br br0   |  grep 'extern_learn.*offload'  |  wc -l")
    assert rc == 0, f"Failed to grep 'extern_learn.*offload'.\n"

    amount = int(out) - ixia_vhost_mac_count
    err_msg = f"Expected count of extern_learn offload entities: 4000, Actual count: {amount}"
    assert amount  == 4000, err_msg

    out = await BridgeFdb.show(input_data=[{device_host_name: [{"options": "-j"}]}],
                               parse_output=True)
    assert out[0][device_host_name]["rc"] == 0, "Failed to get fdb entry.\n"

    fdb_entries = out[0][device_host_name]["parsed_output"]
    learned_macs = [en["mac"] for en in fdb_entries if "mac" in en]
    list_macs = ["00:00:00:00:00:35", "00:00:00:08:f0:35"]
    for mac in list_macs:
        err_msg = f"Expected MACs are not found in FDB, but found MACs:{out}\n"
        assert mac in learned_macs, err_msg
