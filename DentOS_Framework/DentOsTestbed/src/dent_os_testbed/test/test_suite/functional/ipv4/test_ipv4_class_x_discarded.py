import asyncio
import pytest

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

pytestmark = pytest.mark.suite_functional


async def _run_test(tgen_dev, dent_dev, address_map, expected_loss):
    # 1. Init interfaces
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

    # 5. Generate traffic and verify packets have been discarded/forwarded
    streams = {
        f"{tg_ports[0]} -> {tg_ports[1]}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
        },
    }
    await tgen_utils_setup_streams(tgen_dev, None, streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == expected_loss

    await tgen_utils_stop_protocols(tgen_dev)


@pytest.mark.asyncio
async def test_ipv4_class_a_dis(testbed):
    """
    Test Name: test_ipv4_class_a_dis
    Test Suite: suite_functional_ipv4
    Test Overview: Test discard class_A ip
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Enable IPv4 forwarding
    4. Configure IP addrs
    5. Generate traffic and verify packets have been discarded
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]

    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "1.1.1.1", "1.1.1.2", 8),
        (ports[1], tg_ports[1], "0.0.0.1", "0.0.0.2", 8),
    )

    await _run_test(tgen_dev, dent_dev, address_map, 100)


@pytest.mark.asyncio
async def test_ipv4_class_b_dis(testbed):
    """
    Test Name: test_ipv4_class_b_dis
    Test Suite: suite_functional_ipv4
    Test Overview: Test forward class_B ip
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Enable IPv4 forwarding
    4. Configure IP addrs
    5. Generate traffic and verify packets have been forwarded
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]

    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "128.1.1.1", "128.1.1.2", 16),
        (ports[1], tg_ports[1], "191.255.1.1", "191.255.1.2", 16),
    )

    await _run_test(tgen_dev, dent_dev, address_map, 0)


@pytest.mark.asyncio
async def test_ipv4_class_c_dis(testbed):
    """
    Test Name: test_ipv4_class_c_dis
    Test Suite: suite_functional_ipv4
    Test Overview: Test forward class_C ip
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Enable IPv4 forwarding
    4. Configure IP addrs
    5. Generate traffic and verify packets have been forwarded
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]

    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "192.1.1.1", "192.1.1.2", 24),
        (ports[1], tg_ports[1], "223.255.255.1", "223.255.255.2", 24),
    )

    await _run_test(tgen_dev, dent_dev, address_map, 0)


@pytest.mark.asyncio
async def test_ipv4_class_e_dis(testbed):
    """
    Test Name: test_ipv4_class_e_dis
    Test Suite: suite_functional_ipv4
    Test Overview: Test discard class_E ip
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Enable IPv4 forwarding
    4. Configure IP addrs
    5. Generate traffic and verify packets have been discarded
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    dent = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[dent][0]
    ports = tgen_dev.links_dict[dent][1]

    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "240.0.0.0", "240.0.0.1", 32),
        (ports[1], tg_ports[1], "223.255.254.1", "223.255.254.2", 32),
    )

    await _run_test(tgen_dev, dent_dev, address_map, 100)
