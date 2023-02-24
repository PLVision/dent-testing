import pytest
import asyncio

from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss
)

pytestmark = [
    pytest.mark.suite_functional_bridging,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")
]

async def test_bridging_robustness_macs(testbed):
    """
    Test Name: test_bridging_robustness_macs
    Test Suite: suite_functional_bridging
    Test Overview: Verify that robustness macs learning.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set entities swp1, swp2, swp3, swp4 UP state.
    4.  Set bridge br0 admin state UP.
    5.  Set ports swp1, swp2, swp3, swp4 learning ON.
    6.  Set ports swp1, swp2, swp3, swp4 flood OFF.
    7.  Send traffic to swp1 to learn source increment address
        00:00:00:00:00:35 with step '00:00:00:00:10:00' and count 4000.
    8.  Verify that address have been learned and removed from previous learned port.
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
    traffic_duration = 15
    ixia_vhost_mac_count = 4
    #define base on test stability
    num = 4000

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
            {"device": port, "learning": True, "True": False} for port in ports]}])
    err_msg = f"Verify that entities set to learning 'ON' and flooding 'OFF' state.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    address_map = (
        # swp port, tg port,    tg ip,     gw,        plen
        (ports[0], tg_ports[0], "1.1.1.2", "1.1.1.1", 24),
        (ports[1], tg_ports[1], "1.1.1.3", "1.1.1.1", 24),
        (ports[2], tg_ports[2], "1.1.1.4", "1.1.1.1", 24),
        (ports[3], tg_ports[3], "1.1.1.5", "1.1.1.1", 24),
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
                   "count": num},
            "dstMac": "aa:bb:cc:dd:ee:11",
            "type": "raw",
            "protocol": "802.1Q",
            "rate": "1000",
        },
        "streamB": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[2]][0]["name"],
            "srcMac": {"type": "increment",
                   "start": "00:00:00:00:00:35",
                   "step": "00:00:00:00:10:00",
                   "count": num},
            "dstMac": "aa:bb:cc:dd:ee:12",
            "type": "raw",
            "protocol": "802.1Q",
            "rate": "1000",
        },
        "streamC": {
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "srcMac": {"type": "increment",
                   "start": "00:00:00:00:00:35",
                   "step": "00:00:00:00:10:00",
                   "count": num},
            "dstMac": "aa:bb:cc:dd:ee:13",
            "type": "raw",
            "protocol": "802.1Q",
            "rate": "1000",
        },
        "streamD": {
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "srcMac": {"type": "increment",
                   "start": "00:00:00:00:00:35",
                   "step": "00:00:00:00:10:00",
                   "count": num},
            "dstMac": "aa:bb:cc:dd:ee:14",
            "type": "raw",
            "protocol": "802.1Q",
            "rate": "1000",
        }
    }

    for _ in range(8):
        await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        # check the traffic stats
        stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
        for row in stats.Rows:
            assert tgen_utils_get_loss(row) == 0.000, f'Failed>Loss percent: {row["Loss %"]}'

        rc, out = await dent_dev.run_cmd("bridge fdb show br br0   |  grep 'extern_learn.*offload'  |  wc -l")
        assert rc == 0, f"Failed to grep 'extern_learn.*offload'.\n"

        amount = int(out) - ixia_vhost_mac_count
        err_msg = f"Expected count of extern_learn offload entities: 4000, Actual count: {amount}"
        assert amount  == num, err_msg
