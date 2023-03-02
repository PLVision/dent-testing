import asyncio
import pytest

from dent_os_testbed.lib.bridge.bridge_mdb import BridgeMdb
from dent_os_testbed.lib.bridge.bridge_link import BridgeLink
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = [pytest.mark.suite_functional_igmp,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]


async def get_bridge_mdb(device_name, options="-d -s -j"):
    """
    Get parsed bridge Mdb entries
    Args:
        device_name (str): Dent device host_name
        options (str): Options to pass to bridge cmd
    Returns:
        Dictinary with parsed mdb and router entries
    """

    out = await BridgeMdb.show(
        input_data=[{device_name: [
            {"options": options}]}], parse_output=True)
    err_msg = f"Verify bridge mdb show cmd was successful \n{out}"
    assert out[0][device_name]["rc"] == 0, err_msg

    router_entires = out[0][device_name]["parsed_output"][0]["router"]
    mdb_entires = out[0][device_name]["parsed_output"][0]["mdb"]
    return mdb_entires, router_entires


async def common_bridge_and_igmp_setup(device_name, bridge, igmp_ver, dut_ports, querier_interval=0):
    """
    Common setup part for bridge and igmp
    Args:
        device_name (str): Dent device host name
        bridge (str): Bridge device name
        igm_ver (int): IGMP Version to set on bridge dev
        dut_ports (list): List containing Dent device ports
        querier_interval (int): Multicast querier_interval to be set
    """

    out = await IpLink.add(
        input_data=[{device_name: [
            {"device": bridge, "type": "bridge", "vlan_filtering": 1}]}])
    err_msg = f"Verify that bridge created and vlan filtering set successful\n{out}"
    assert out[0][device_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_name: [
            {"device": bridge, "operstate": "up"}]}])
    err_msg = f"Verify that bridge set to 'UP' state.\n{out}"
    assert out[0][device_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_name: [
            {"device": bridge, "type": "bridge", "mcast_snooping": 1, "mcast_igmp_version": igmp_ver}]}])
    err_msg = f"Verify that bridge set mcast_snooping 1 and mcast_igmp_version {igmp_ver}.\n{out}"
    assert out[0][device_name]["rc"] == 0, err_msg

    if querier_interval:
        out = await IpLink.set(
            input_data=[{device_name: [
                {"device": bridge, "type": "bridge", "mcast_querier": 1, "mcast_querier_interval": querier_interval * 100}]}])
        err_msg = f"Verify that bridge set mcast_querier 1 and mcast_querier_interval to {querier_interval * 100}.\n{out}"
        assert out[0][device_name]["rc"] == 0, err_msg

    out = await IpLink.set(
        input_data=[{device_name: [
            {"device": port, "master": bridge, "operstate": "up"} for port in dut_ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_name]["rc"] == 0, err_msg


@pytest.mark.parametrize("igmp_ver, igmp_msg_ver", [(2, 2), (3, 3), (2, 1), (3, 1), (3, 2)])
async def test_igmp_snooping(testbed, igmp_ver, igmp_msg_ver):
    """
    Test Name: test_igmp_snooping
    Test Suite: suite_functional_igmp
    Test Overview: Test IGMP snooping mixed and identical versions
    Test Procedure:
    1. Create bridge and enable IGMP Snooping, enslave all TG ports to bridge interface \
       Config Fastleave on 1st rx_port
    2. Init interfaces and create 2 mcast Streams
    3. Create 3 membership report streams, 1 with invalid checksum
    4. Send Traffic from router port and from clients
    5. Verify Mdb entries were created from clients
    6. Verify the multicast traffic is flooded to all bridge ports
    7. Stop traffic, create a general query stream from tx_port and send traffic
    8. Verify MDB entries were created for router
    9. Verify the traffic is forwarded to the members only
    10. Create and send Leave stream from 1st rx_port
    11. Verify MDB entry for leave port is deleted and no traffic is received
    """

    bridge = "br0"
    sleep_value = 8
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]

    # 1.Create bridge and enable IGMP Snooping, enslave all TG ports to bridge interface
    # Config Fastleave on 1st rx_port
    await common_bridge_and_igmp_setup(dev_name, bridge, igmp_ver, dut_ports)

    out = await BridgeLink.set(
        input_data=[{dev_name: [
            {"device": dut_ports[1], "fastleave": "on"}]}])
    err_msg = f"Verify that port entities set to fastleave ON.\n{out}"
    assert out[0][dev_name]["rc"] == 0, err_msg

    # 2.Init interfaces and create 2 mcast Streams

    # 3.Create 3 membership report streams, 1 stream with invalid checksum

    # 4.Send Traffic from tx_port and rx_ports
    await asyncio.sleep(sleep_value)

    # 5.Verify MDB entries were created from clients
    mdb_entires, _ = await get_bridge_mdb(dev_name)
    assert len(mdb_entires) == 2, f"Expected 2 Mdb entries, actual count is - {len(mdb_entires)}"
    # Could be added more precise check, by port and grp addr

    # 6.Verify the multicast traffic is flooded to all bridge ports
    await asyncio.sleep(sleep_value)

    # 7.Stop traffic, create a general query stream from tx_port and send traffic
    await asyncio.sleep(sleep_value)

    # 8.Verify MDB entries were created for router
    _, router_entires = await get_bridge_mdb(dev_name)
    assert len(router_entires), f"No MDB router entries were added to bridge MDB table {router_entires}"

    # 9.Verify the traffic is forwarded to the members only

    # 10.Create and send Leave stream from first rx_port
    await asyncio.sleep(sleep_value)

    # 11.Verify its MDB entry is deleted and no traffic is received
    mdb_entires, _ = await get_bridge_mdb(dev_name)
    for entry in mdb_entires:
        assert dut_ports[1] != entry["port"], f"Mdb entry of port {dut_ports[1]} still exists: \n{mdb_entires}"

    #Verify no traffic is received on the port that left the group


async def test_igmp_snooping_modified_query(testbed):
    """
    Test Name: test_igmp_querier
    Test Suite: suite_functional_igmp
    Test Overview: Test IGMP snooping with modified querier interval
    Test Procedure:
    1. Create a bridge and enable IGMP Snooping, enable querrier and change query interval \
       Enslave all TG ports to bridge interface and config fastleave on 1st rx_port
    2. Init interfaces and create 2 multicast Streams
    3. Create 3 membership report streams, 1 with invalid checksum
    4. Send Traffic from router port and from clients
    5. Verify Mdb entries were created for clients and router
    6. Verify the multicast traffic is flooded to all bridge ports except last client
    7. Create and send leave stream from 1st client
    8. Verify MDB entry is deleted
    9. Verify no traffic is received on the port that left the group
    """

    bridge = "br0"
    querrier_interval = 10
    sleep_value = 5
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]

    # 1.Create a bridge and enable IGMP Snooping, enable querrier and change query interval
    #   Config Fastleave on 1st rx_port
    await common_bridge_and_igmp_setup(dev_name, bridge, 2, dut_ports, querier_interval=querrier_interval)

    out = await BridgeLink.set(
        input_data=[{dev_name: [
            {"device": dut_ports[1], "fastleave": "on"}]}])
    err_msg = f"Verify that port entities set to fastleave ON.\n{out}"
    assert out[0][dev_name]["rc"] == 0, err_msg

    # 2.Init interfaces and create 2 multicast Streams

    # 3.Create 3 membership report streams, 1 with invalid checksum

    # 4.Send Traffic from router port and from clients
    await asyncio.sleep(querrier_interval + 5)

    # 5.Verify Mdb entries were created for clients and router
    mdb_entires, router_entires = await get_bridge_mdb(dev_name)
    assert len(mdb_entires) == 2, f"Expected 2 Mdb entries, actual count is - {len(mdb_entires)}"
    assert len(router_entires), f"No MDB router entries were added to bridge MDB table {router_entires}"

    # 6.Verify the multicast traffic is flooded to all bridge ports except last client

    # 7.Create and send leave stream from 1st client
    await asyncio.sleep(sleep_value)

    # 8.Verify MDB entry is deleted
    mdb_entires, _ = await get_bridge_mdb(dev_name)
    for entry in mdb_entires:
        assert dut_ports[1] != entry["port"], f"Mdb entry of port {dut_ports[1]} still exists: \n{mdb_entires}"

    # 9.Verify no traffic is received on the port that left the group


async def test_igmp_snooping_diff_source_addrs(testbed):
    """
    Test Name: test_igmp_snooping_diff_sources
    Test Suite: suite_functional_igmp
    Test Overview: Test IGMP snooping with different source addrs
    Test Procedure:
    1. Create a bridge and enable IGMP Snooping v3, \
       Enslave all TG ports to bridge interface and set all interfaces to up state
    2. Init interfaces, create 4 multicast streams and 1 general query
    3. Generate 3 Membership reports from the clients, 1 with invalid Checksum
    4. Send Traffic from router port and from clients
    5. Verify Mdb entries were created from clients and router
    6. Verify the multicast traffic is flooded to the client #1 and #2 only
    7. Statically un-subscribe client #1 from multicast group 227.1.1.1
    8. Verify the Mdb entry for client #1 is deleted
    9. Verify the traffic is not forwarded to client #1 and still is to client #2
    """

    bridge = "br0"
    mcast_group1 = "227.1.1.1"
    sleep_value = 5
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dev_name = dent_devices[0].host_name
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]

    # 1.Create a bridge and enable IGMP Snooping v3,
    #   Enslave all TG ports to bridge interface and set all interfaces to up state
    await common_bridge_and_igmp_setup(dev_name, bridge, 3, dut_ports)

    # 2.Init interfaces, create 4 multicast streams and 1 general query

    # 3.Generate 3 Membership reports from the clients, 1 with invalid checksum

    # 4.Send Traffic from router port and from clients
    await asyncio.sleep(sleep_value)

    # 5.Verify Mdb entries were created from clients and router
    mdb_entires, router_entires = await get_bridge_mdb(dev_name)
    assert len(mdb_entires) == 4, f"Expected 2 Mdb entries, actual count is - {len(mdb_entires)}"
    assert len(router_entires), f"No MDB router entries were added to bridge MDB table {len(router_entires)}"

    # 6.Verify the multicast traffic is flooded to the client #1 and #2 only
    await asyncio.sleep(sleep_value)

    # 7.Statically un-subscribe client #1 from multicast group 227.1.1.1
    out = await BridgeMdb.delete(
        input_data=[{dev_name: [
            {"dev": bridge, "port": dut_ports[1], "group": mcast_group1, "vid": 1}]}])
    err_msg = f"Verify that Mdb entry was successfully deleted\n{out}"
    assert out[0][dev_name]["rc"] == 0, err_msg
    await asyncio.sleep(sleep_value)

    # 8.Verify the Mdb entry for client #1 is deleted
    mdb_entires, _ = await get_bridge_mdb(dev_name)
    assert len(mdb_entires) == 2, f"Mdb entries are not as expected {len(mdb_entires)}"

    # 9.Verify the traffic is not forwarded to client #1 and still is to client #2
