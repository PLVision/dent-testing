import pytest, asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ethtool.ethtool import Ethtool

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_get_traffic_stats,
    tgen_utils_update_l1_config,
    tgen_utils_setup_streams,
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_get_loss
)

from dent_os_testbed.utils.test_utils.tb_utils import tb_get_qualified_ports

pytestmark = [pytest.mark.suite_functional_l1,
              pytest.mark.asyncio,
              pytest.mark.usefixtures("cleanup_bridges", "cleanup_tgen")]

@pytest.mark.parametrize("speed, duplex, speed_ixia, duplex_ixia",
                         [
                            pytest.param(10, "full", 10, "half"),
                            pytest.param(10, "full", 100, "full"),
                            pytest.param(10, "full", 100, "half"),
                            pytest.param(10, "full", 1000, "full"),

                            pytest.param(10, "half", 10, "full"),
                            pytest.param(10, "half", 100, "full"),
                            pytest.param(10, "half", 100, "half"),
                            pytest.param(10, "half", 1000, "full"),

                            pytest.param(100, "full", 10, "full"),
                            pytest.param(100, "full", 10, "half"),
                            pytest.param(100, "full", 100, "half"),
                            pytest.param(100, "full", 1000, "full"),

                            pytest.param(100, "half", 10, "full"),
                            pytest.param(100, "half", 10, "half"),
                            pytest.param(100, "half", 100, "full"),
                            pytest.param(100, "half", 1000, "full"),

                            pytest.param(1000, "full", 10, "full"),
                            pytest.param(1000, "full", 10, "half"),
                            pytest.param(1000, "full", 100, "full"),
                            pytest.param(1000, "full", 100, "half")
                         ])

async def test_l1_mixed_speed(testbed, speed, duplex, speed_ixia, duplex_ixia):
    """
    Test Name: test_l1_mixed_speed
    Test Suite: suite_functional_l1
    Test Overview: Verify the port link status setting and the port speed setting.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Init bridge entity br0.
    2.  Set ports swp1, swp2, swp3, swp4 master br0.
    3.  Set bridge br0 admin state UP.
    4.  Set entities swp1, swp2, swp3, swp4 UP state.
    5.  Configure dut ports:
            speed -> speed
            autoneg -> Off
            duplex -> duplex [On/Off]
        Configure ixia ports:
            speed -> speed_ixia
            duplex -> duplex_ixia [On/Off]
            autoneg -> Off
    6.  Send traffic by TG.
    7.  Verify port duplex and speed as they were configured.
    8.  Set up the traffic rate according to duplex mode.
    9.  Verify no packet loss occurred and all transmitted traffic received.
    """

    bridge = "br0"
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip("The testbed does not have enough dent with tgen connections")
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    tg_ports = tgen_dev.links_dict[device_host_name][0]
    ports = tgen_dev.links_dict[device_host_name][1][:2]
    timeout = 20

    speed_ports = await tb_get_qualified_ports(dent_dev, ports, speed, duplex)

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
        {"device": port, "operstate": "up", "master": bridge} for port in ports]}])
    err_msg = f"Verify that bridge entities set to 'UP' state and links enslaved to bridge.\n{out}"
    assert out[0][device_host_name]["rc"] == 0, err_msg

    out = await Ethtool.set(
        input_data=[{device_host_name: [
        {"devname": port, "speed": speed, "autoneg": "off", "duplex": duplex} for port in ports]}])
    assert out[0][device_host_name]["rc"] == 0, f"Verify set-up settings for port duplex and speed.\n{out}"

    dev_groups = tgen_utils_dev_groups_from_config(
        [{"ixp": tg_ports[0], "ip": "100.1.1.2", "gw": "100.1.1.6", "plen": 24},
         {"ixp": tg_ports[1], "ip": "100.1.1.3", "gw": "100.1.1.6", "plen": 24}])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, ports, dev_groups)

    # configure ixia ports
    await tgen_utils_update_l1_config(tgen_dev, tg_ports, speed=speed_ixia, duplex=duplex_ixia, autoneg=False)
    # wait needed in case port was down before
    await asyncio.sleep(timeout)

    # verify port duplex and speed was configured
    for port in ports:
        out = await Ethtool.show(input_data=[{device_host_name: [{"devname": port}]}], parse_output=True)
        assert speed == int(out[0][device_host_name]['parsed_output']['speed'][:-4]), "Failed speed test"
        assert duplex.capitalize() == out[0][device_host_name]['parsed_output']['duplex'], "Failed duplex test"

    # set up traffic according to duplex mode
    supported_speed_ports = [name for name in speed_ports.keys()]
    first_port_index = ports.index(supported_speed_ports[0])
    second_port_index = ports.index(supported_speed_ports[1])

    streams = {f"{tg_ports[first_port_index]} --> {tg_ports[second_port_index]}": {
        "type": "ethernet",
        "ep_source": ports[first_port_index],
        "ep_destination": ports[second_port_index],
        "frame_type": "line_rate",
        "rate": 100 if duplex == "full" else 50
       },
        f"{tg_ports[second_port_index]} --> {tg_ports[first_port_index]}": {
        "type": "ethernet",
        "ep_source": ports[second_port_index],
        "ep_destination": ports[first_port_index],
        "frame_type": "line_rate",
        "rate": 100 if duplex == "full" else 50
       }}

    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(timeout/20)
    await tgen_utils_stop_traffic(tgen_dev)

    # check the traffic stats
    stats = await tgen_utils_get_traffic_stats(tgen_dev, "Traffic Item Statistics")
    for row in stats.Rows:
        assert tgen_utils_get_loss(row) == 0.000, \
            f"Verify that traffic from {row['Tx Port']} to {row['Rx Port']} forwarded.\n{out}"
