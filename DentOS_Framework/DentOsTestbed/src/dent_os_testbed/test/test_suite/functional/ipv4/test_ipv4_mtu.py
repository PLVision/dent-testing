import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ethtool.ethtool import Ethtool

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


@pytest.mark.asyncio
async def test_ipv4_oversized_mtu(testbed):
    """
    Test Name: test_ipv4_oversized_mtu
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 oversized mtu counters
    Test Procedure:
    1. Init interfaces
    2. Configure ports up
    3. Enable IPv4 forwarding
    4. Configure IP addrs
    5. Configure interfaces MTU to 1000
    6. Generate traffic with packet size 1200 and verify there's no reception due to MTU
    7. Verify oversized counter been incremented in port statistics
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
    def_mtu_map = []
    mtu = 1000
    address_map = (
        # swp port, tg port,    swp ip,    tg ip,     plen
        (ports[0], tg_ports[0], "1.1.1.1", "1.1.1.2", 24),
        (ports[1], tg_ports[1], "2.2.2.1", "2.2.2.2", 24),
        (ports[2], tg_ports[2], "3.3.3.1", "3.3.3.2", 24),
        (ports[3], tg_ports[3], "4.4.4.1", "4.4.4.2", 24),
    )
    tg_to_swp_map = {
        tg: swp for swp, tg, _, _, _ in address_map
    }

    # 2. Configure ports up
    out = await IpLink.set(input_data=[{dent: [
        {"device": port, "operstate": "up"}
        for port, _, _, _, _ in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to set port state UP"

    # 3. Enable IPv4 forwarding
    rc, out = await dent_dev.run_cmd(f"sysctl -n net.ipv4.ip_forward=1")
    assert rc == 0, "Failed to enable ip forwarding"

    # 4. Configure IP addrs
    out = await IpAddress.add(input_data=[{dent: [
        {"dev": port, "prefix": f"{ip}/{plen}"}
        for port, _, ip, _, plen in address_map
    ]}])
    assert out[0][dent]["rc"] == 0, "Failed to add IP addr to port"

    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        f"{tg1} <-> {tg2}": {
            "type": "ipv4",
            "ip_source": dev_groups[tg1][0]["name"],
            "ip_destination": dev_groups[tg2][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "bi_directional": True,
            "frameSize": mtu + 200,
        } for tg1, tg2 in (tg_ports[:2], tg_ports[2:])
    }

    try:
        await tgen_utils_setup_streams(tgen_dev, None, streams)

        # 5. Configure interfaces MTU to 1000
        out = await IpLink.show(input_data=[{dent: [
            {"cmd_options": "-j"}
        ]}], parse_output=True)
        assert out[0][dent]["rc"] == 0, "Failed to get ports"

        def_mtu_map = [link for link in out[0][dent]["parsed_output"] if link["ifname"] in ports]

        out = await IpLink.set(input_data=[{dent: [
            {"device": port, "mtu": mtu} for port in ports
        ]}])
        assert out[0][dent]["rc"] == 0, "Failed to set port mtu"

        # 6. Generate traffic with packet size 1200
        old_stats = {}
        for port in ports:
            out = await Ethtool.show(input_data=[{dent: [
                {"devname": port, "options": "-S"}
            ]}], parse_output=True)
            assert out[0][dent]["rc"] == 0
            old_stats[port] = out[0][dent]["parsed_output"]

        await tgen_utils_start_traffic(tgen_dev)
        await asyncio.sleep(traffic_duration)
        await tgen_utils_stop_traffic(tgen_dev)

        stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
        for row in stats.Rows:
            # Verify there's no reception due to MTU
            loss = tgen_utils_get_loss(row)
            assert loss == 100, f"Expected loss: 100%, actual: {loss}%"

            # 7. Verify oversized counter been incremented in port statistics
            swp = tg_to_swp_map[row["Rx Port"]]
            out = await Ethtool.show(input_data=[{dent: [
                {"devname": swp, "options": "-S"}
            ]}], parse_output=True)
            assert out[0][dent]["rc"] == 0

            new_stats = out[0][dent]["parsed_output"]
            oversized = int(new_stats["oversize"]) - int(old_stats[port]["oversize"])
            assert oversized == int(row["Tx Frames"])

    finally:
        await tgen_utils_stop_protocols(tgen_dev)

        # Restore mtu
        out = await IpLink.set(input_data=[{dent: [
            {"device": link["ifname"], "mtu": link["mtu"]} for link in def_mtu_map
        ]}])
        assert out[0][dent]["rc"] == 0, "Failed to set port mtu"

        # Flush ip addr
        out = await IpAddress.flush(input_data=[{dent: [
            {"dev": port} for port in ports
        ]}])
        assert out[0][dent]["rc"] == 0, "Failed to clear ip addr"
