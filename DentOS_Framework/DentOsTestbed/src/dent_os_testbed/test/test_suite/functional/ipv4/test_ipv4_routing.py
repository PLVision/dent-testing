import itertools
import asyncio
import pytest
import random

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_stop_protocols,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
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
