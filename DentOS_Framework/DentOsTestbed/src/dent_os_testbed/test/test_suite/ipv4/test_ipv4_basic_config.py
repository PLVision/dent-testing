import asyncio
import pytest

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_neighbor import IpNeighbor
from dent_os_testbed.lib.traffic.ixnetwork.ixnetwork_ixia_client_impl import IxnetworkIxiaClientImpl

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_connect_to_tgen,
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_get_traffic_stats,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_protocols,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss,
    tgen_utils_dev_groups_from_config,
    tgen_utils_traffic_generator_connect,
    tgen_utils_get_swp_info,
)

pytestmark = pytest.mark.suite_functional_ipv4


@pytest.mark.asyncio
async def test_ipv4_basic_config(testbed):
    """
    Test Name: test_ipv4_basic_config
    Test Suite: suite_functional_ipv4
    Test Overview: Test IPv4 basic configuration
    Test Procedure:
    1. Add IP address for 4 interfaces in different subnets.
    2. Verify that: a) no errors arise on IP address adding;
                    b) connected routes added and offloaded.
    3. Set ip_forwarding=1 on host
    4. Send bidirectional traffic between TG ports: a) 1 and 2 with default TTL;
                                                    b) 3 and 4 with TTL 1.
    5. Verify that: a) there is no packet loss between ports 1 and 2;
                    b) there is 100% loss between ports 3 and 4.
    6. Clear ARP on DUT.
    7. Send traffic with unknown DST IP to one direction and Known to another.
    8. Verify that 100% of packets lost for unknown DSP IP and there is no loss for known Dst IP.
    9. Delete IP addresses on DUT and send traffic. Leave one IP prefix on the 1st port.
    10. Verify that: a) no errors on IP prefix delete;
                     b) connected routes are deleted;
                     c) ARPs are flushed;
                     d) 100% packets loss.
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

    out = await IpAddress.flush(input_data=[{dent: [{"dev": port} for port in ports]}])
    assert out[0][dent]["rc"] == 0
    out = await IpLink.set(input_data=[{dent: [{"device": port, "operstate": "up"} for port in ports]}])
    assert out[0][dent]["rc"] == 0

    address_map = (
        #swp port, tg port,     swp ip,     tg ip,      plen
        (ports[0], tg_ports[0], "12.0.0.1", "12.0.0.2", 24),
        (ports[1], tg_ports[1], "13.0.0.1", "13.0.0.2", 20),
        (ports[2], tg_ports[2], "14.0.0.1", "14.0.0.2", 30),
        (ports[3], tg_ports[3], "15.0.0.1", "15.0.0.2", 16),
        (ports[0], tg_ports[0], "16.0.0.1", "16.0.0.2", 8),
    )

    # 1. Add IP address for 4 interfaces in different subnets
    out = await IpAddress.add(input_data=[{dent: [
        {"dev": port, "prefix": f"{ip}/{plen}"}
        for port, _, ip, _, plen in address_map
    ]}])

    # 2.a Verify that no errors arise on IP address adding
    assert out[0][dent]["rc"] == 0

    # 2.b Verify that connected routes added and offloaded
    out = await IpRoute.show(input_data=[{dent: [{"cmd_options": "-j"}]}],
                             parse_output=True)
    assert out[0][dent]["rc"] == 0

    for route in out[0][dent]["parsed_output"]:
        if route.get("dev", None) in ports:
            assert "offload" in route["flags"], "Some routes are not offloaded"

    # 3. Set ip_forwarding=1 on host
    rc, out = await dent_dev.run_cmd("sysctl -n net.ipv4.ip_forward=1")
    assert rc == 0

    # 4. Send bidirectional traffic between TG ports
    dev_groups = tgen_utils_dev_groups_from_config(
        {"ixp": port, "ip": ip, "gw": gw, "plen": plen}
        for _, port, gw, ip, plen in address_map
    )

    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, ports[1], swp_info)

    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    streams = {
        # 4.a 1 and 2 with default TTL
        "ipv4": {
            "type": "ipv4",
            "ip_source": dev_groups[tg_ports[0]][0]["name"],
            "ip_destination": dev_groups[tg_ports[1]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "bi_directional": True,
        },
        # 4.b 3 and 4 with TTL 1
        "ipv4_ttl_1": {
            "type": "ipv4",
            "ip_source": dev_groups[tg_ports[2]][0]["name"],
            "ip_destination": dev_groups[tg_ports[3]][0]["name"],
            "protocol": "ip",
            "rate": "1000",  # pps
            "bi_directional": True,
        },
        "ipv4_unknown": {
            "type": "raw",
            "ip_source": dev_groups[tg_ports[1]][0]["name"],
            "ip_destination": dev_groups[tg_ports[0]][0]["name"],
            "srcIp": dev_groups[tg_ports[1]][0]["ip"],
            "dstIp": "192.168.10.20",
            "srcMac": "02:00:00:00:00:01",
            "dstMac": swp_info["mac"],
            "protocol": "ip",
            "rate": "1000",  # pps
        },
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # Set TTL for stream ipv4_ttl_1
    for ti in IxnetworkIxiaClientImpl.tis:
        if ti.Name != "ipv4_ttl_1":
            continue
        config_element = ti.ConfigElement.find()
        field = config_element.Stack.find("IPv4").Field.find(Name="ttl")
        # The correct way to update the packets` TTL would be to call field.update(SingleValue="1").
        # So, we would make a REST call to `/api/v1/*blah blah*/field/24`, where field/24
        # is refering to the packet TTL for the stream. The `SingleValue` is passed as a payload.
        # But the ixnetwork framework does some manipulation with the url (see ixnetwork_restpy/base.py:399).
        # The new url will now look like this: `/api/v1/*blah blah*/field`. The field id is moved from
        # url to payload, which is okay with other fields (like IP or MAC), but it`s not okay with TTL.
        # So, for now use this as a workaround.
        field._connection._update(field.href, {"singleValue": "1"})
        ti.Generate()
    IxnetworkIxiaClientImpl.ixnet.Traffic.Apply()

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 5. Verify that: a) there is no packet loss between ports 1 and 2;
    #                 b) there is 100% loss between ports 3 and 4.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        if row["Traffic Item"] == "ipv4":
            assert tgen_utils_get_loss(row) == 0.000
        elif row["Traffic Item"] == "ipv4_ttl_1":
            assert tgen_utils_get_loss(row) == 100.000

    # 6. Clear ARP on DUT.
    out = await IpNeighbor.flush(input_data=[{dent: [{"nud": "all"}]}])
    assert out[0][dent]["rc"] == 0

    # 7. Send traffic with unknown DST IP to one direction and Known to another.
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    # 8. Verify that 100% of packets lost for unknown DSP IP and there is no loss for known Dst IP.
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        if row["Traffic Item"] == "ipv4":
            assert tgen_utils_get_loss(row) == 0.000
        elif row["Traffic Item"] == "ipv4_unknown":
            assert tgen_utils_get_loss(row) == 100.000

    # 9. Delete IP addresses on DUT and send traffic. Leave one IP prefix on the 1st port
    out = await IpAddress.delete(input_data=[{dent: [
        {"dev": port, "prefix": f"{ip}/{plen}"}
        for port, _, ip, _, plen in address_map[:-1]
    ]}])

    # 10.a Verify that there are no errors on IP prefix delete
    assert out[0][dent]["rc"] == 0

    # 10.b Verify that connected routes are deleted
    out = await IpRoute.show(input_data=[{dent: [{"cmd_options": "-j"}]}],
                             parse_output=True)
    assert out[0][dent]["rc"] == 0
    for route in out[0][dent]["parsed_output"]:
        if not "dev" in route:
            continue
        if route["dev"] == ports[0]:
            # port #0 should have only one route
            assert address_map[-1][2][:-1] in route["dst"]
        else:
            assert route["dev"] not in ports

    # 10.c Verify that ARPs are flushed
    out = await IpNeighbor.show(input_data=[{dent: [{"cmd_options": "-j"}]}],
                                parse_output=True)
    assert out[0][dent]["rc"] == 0
    for nei in out[0][dent]["parsed_output"]:
        if nei.get("dev", None) in ports:
            assert "FAILED" in nei["state"]

    # 10.d Verify 100% packets loss.
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)

    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Flow Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 100.000

    await tgen_utils_stop_protocols(tgen_dev)
