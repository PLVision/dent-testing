import asyncio
import pytest

from random import randint

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen,
    tgen_utils_traffic_generator_connect,
    tgen_utils_dev_groups_from_config,
    tgen_utils_setup_streams,
    tgen_utils_get_swp_info,
    tgen_utils_clear_traffic_items,
    tgen_utils_get_traffic_stats,
    tgen_utils_get_loss,
)

from dent_os_testbed.test.test_suite.functional.ifupdown2.ifupdown2_utils import (
    INTERFACES_FILE, IPV4_TEMPLATE,
    FDB_TEMPLATE, LACP_TEMPLATE,
    reboot_and_wait, conf_ecmp,
    gen_random_ip_net,
    write_reload_check_ifupdown_config,
    verify_ip_address_routes,
    start_and_stop_stream,
    format_mac, inc_mac,
    random_mac, check_vlan_members,
    config_bridge, check_member_devices,
)
from dent_os_testbed.test.test_suite.functional.ecmp.test_ecmp import verify_ecmp_distribution

pytestmark = [
    pytest.mark.suite_functional_ifupdown2,
    pytest.mark.asyncio,
]


@pytest.mark.usefixtures('enable_ipv4_forwarding')
async def test_ifupdown2_ipv4_ecmp(testbed, prepare_env):
    """
    Test Name: test_ifupdown2_ipv4_ecmp
    Test Suite: suite_functional_ifupdown2
    Test Overview: Test ifupdown2 with bidirectional traffic and Ecmp route
    Test Procedure:
    1. Prepare ifupdown2 environment config
    2. Prepare ifupdown2 config: create 2 ipv4 addresses and configure ECMP route with random network to exit via the RIFs' neighbors
    3. Verify no errors in ifupdown2 config, apply config, compare running ifupdown2 config vs default config
    4. Init interfaces and connect devices
    5. Setup bidirectional stream and define stream with incremented ip dst for ecmp
    6. Verify ip addr exists for each RIF and route is present, verify ECMP route exist and offloaded
    7. Transmit bidirectional stream for traffic duration
    8. Verify all traffic is forwarded to each host without packet loss
    9. Clear previous traffic items, setup ECMP traffic and transmit traffic
    10. Verify traffic is distributed beetwen ECMP nexthops
    11. Reboot DUT
    12. Compare running ifupdown2 config vs default config
    13. Verify ip addr exists for each RIF and route is present, verify ECMP route exist and offloaded
    14. Transmit ECMP traffic for a traffic duration time
    15. Verify traffic is distributed beetwen ECMP nexthops
    16. Clear previous traffic items, setup bidirectional traffic and transmit it for a traffic duration time
    17. Verify all traffic is forwarded to each host without packet loss
    18. Roll back ifupdown configuration to default during fixture teardown
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 3)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    ip_net1, net_1_range = gen_random_ip_net()
    ip_net2, net_2_range = gen_random_ip_net()
    traffic_duration = randint(10, 30)
    full_config = ''

    address_map = (
        (dut_ports[0], tg_ports[0], str(ip_net1[1]), str(ip_net1[-10]), ip_net1.prefixlen),
        (dut_ports[1], tg_ports[1], str(ip_net2[1]), str(ip_net2[-10]), ip_net2.prefixlen),
        (dut_ports[2], tg_ports[2], '2.2.2.1', '2.2.2.5', '24'),
    )

    # 1.Prepare ifupdown2 environment config
    config = {'template_lookuppath': '/etc/network/ifupdown2/templates',
              'addon_syntax_check': 1,
              'default_interfaces_configfile': INTERFACES_FILE
              }
    rc = await prepare_env(dent_dev, config)
    assert not rc, 'Failed to prepare ifupdown2 enviroment config'

    # 2.Prepare ifupdown2 config: create 2 ipv4 adresses and configure ECMP route with random network to exit via the RIFs' neighbors
    full_config += ''.join([IPV4_TEMPLATE.format(name=port, inet='static', address=f'{ip}/{plen}')
                            for port, _, ip, _, plen in address_map])
    route, _ = gen_random_ip_net()
    nexthop1 = ip_net1[randint(2, net_1_range - 10)]
    nexthop2 = ip_net2[randint(2, net_2_range - 10)]
    full_config += conf_ecmp(route, [nexthop1, nexthop2])

    # 3.Verify no errors in ifupdown2 config, apply config, compare running ifupdown2 config vs default config
    await write_reload_check_ifupdown_config(dent_dev, full_config, config['default_interfaces_configfile'])

    # 4.Init interfaces and connect devices
    dev_groups = tgen_utils_dev_groups_from_config(
        {'ixp': port, 'ip': ip, 'gw': gw, 'plen': plen}
        for _, port, gw, ip, plen in address_map
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 5.Setup bidirectional stream and define stream with incremented ip dst for ECMP
    bidirectional_stream = {
        'bidirectional_stream': {
            'type': 'ipv4',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'rate': 100,
            'frame_rate_type': 'line_rate',
            'bi_directional': True,
        }
    }

    swp_info = {}
    await tgen_utils_get_swp_info(dent_dev, dut_ports[2], swp_info)
    ecmp_stream = {'increment_ip_dst': {
        'type': 'raw',
        'protocol': 'ip',
        'ip_source': dev_groups[tg_ports[2]][0]['name'],
        'ip_destination': dev_groups[tg_ports[0]][0]['name'],  # We dont care about ip_dst as we will use port stats
        'srcMac': '00:00:00:02:01:02',
        'dstMac': swp_info['mac'],
        'srcIp': f'1.1.1.{randint(3, 100)}',
        'dstIp': {'type': 'increment',
                  'start': str(route[1]),
                  'step':  '0.0.0.1',
                  'count': 3},
        'frameSize': 200,
        'rate': 100,
        'frame_rate_type': 'line_rate'}
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=bidirectional_stream)

    # 6.Verify ip addr exists for each RIF and route is present, verify ECMP route exist and offloaded
    await verify_ip_address_routes(dev_name, address_map, route)

    # 7.Transmit bidirectional stream for traffic duration
    await start_and_stop_stream(tgen_dev, traffic_duration)

    # 8.Verify all traffic is forwarded to each host without packet loss
    stats = await tgen_utils_get_traffic_stats(tgen_dev, stats_type='Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    # 9.Clear previous traffic items, setup ECMP traffic and transmit traffic
    await tgen_utils_clear_traffic_items(tgen_dev, traffic_names=['bidirectional_stream'])
    await asyncio.sleep(6)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=ecmp_stream)
    await start_and_stop_stream(tgen_dev, traffic_duration)

    # 10.Verify traffic is distributed beetwen ECMP nexthops
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    await verify_ecmp_distribution(stats, tg_ports[2], tg_ports[:2])

    # 11.Reboot DUT
    await reboot_and_wait(dent_dev)

    # 12.Compare running ifupdown2 config vs default config
    rc, out = await dent_dev.run_cmd(f"ifquery -a -c -i {config['default_interfaces_configfile']}")
    assert not rc, f'Unexpected running configuration \n{out}'

    # 13.Verify ip addr exists for each RIF and route is present, verify ECMP route exist and offloaded
    await verify_ip_address_routes(dev_name, address_map, route)

    # 14.Transmit ECMP traffic for a traffic duration time
    await start_and_stop_stream(tgen_dev, traffic_duration)

    # 15.Verify traffic is distributed beetwen ECMP nexthops
    stats = await tgen_utils_get_traffic_stats(tgen_dev)
    await verify_ecmp_distribution(stats, tg_ports[2], tg_ports[:2])

    # 16.Clear previous traffic items, setup bidirectional traffic and transmit it for a traffic duration time
    await tgen_utils_clear_traffic_items(tgen_dev, traffic_names=['increment_ip_dst'])
    await asyncio.sleep(6)
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=bidirectional_stream)
    await start_and_stop_stream(tgen_dev, traffic_duration)

    # 17.Verify all traffic is forwarded to each host without packet loss
    # 18.Roll back ifupdown configuration to default during fixture teardown
    stats = await tgen_utils_get_traffic_stats(tgen_dev, stats_type='Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'


async def test_ifupdown2_bridge(testbed, prepare_env):
    """
    Test Name: test_ifupdown2_bridge
    Test Suite: suite_functional_ifupdown2
    Test Overview: Test ifupdown2 with Bridge device and tagged/untagged traffic
    Test Procedure:
    1. Prepare ifupdown2 environment config
    2. Prepare ifupdown2 config: Add Bridge device, add 4 member ports, add vlans, add fdb entries
    3. Verify no errors in ifupdown2 config, apply config, compare running ifupdown2 config vs default config
    4. Verify that bridge device added with 4 member ports and expected vlans
    5. Init interfaces and connect devices
    6. Setup 1 untagged stream and 3 tagged streams
    7. Transmit streams
    8. Verify that untagged traffic was flooded, tagged traffic switched to expected port without loss
    9. Reboot DUT
    10. Compare running ifupdown2 config vs default config
    11. Verify that bridge device added with 4 member ports and expected vlans
    12. Transmit streams
    13. Verify that untagged traffic was flooded, tagged traffic switched to expected port without loss
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    traffic_duration = randint(10, 30)
    bridge = 'br0'
    num_of_macs = randint(10, 50)
    full_config = ''
    pvid = 1

    # 1.Prepare ifupdown2 environment config
    config = {'template_lookuppath': '/etc/network/ifupdown2/templates',
              'addon_syntax_check': 1,
              'default_interfaces_configfile': INTERFACES_FILE
              }
    rc = await prepare_env(dent_dev, config)
    assert not rc, 'Failed to prepare ifupdown2 enviroment config'

    # 2.Prepare ifupdown2 config: Add Bridge device, add 4 member ports, add vlans, add fdb entries
    vlans = []
    collected_mac = {}
    start_vlan = 100
    for indx, port in enumerate(dut_ports[1:]):
        collected_mac[port] = {'vlan': start_vlan + indx, 'mac': format_mac(port, start_vlan + indx)}
        vlans.append(start_vlan + indx)

    full_config += config_bridge(bridge, dut_ports, vlan_aware=True, pvid=pvid,
                                 vlans=[str(collected_mac[i]['vlan']) for i in collected_mac])

    for port in collected_mac:
        for i in range(num_of_macs):
            full_config += FDB_TEMPLATE.format(mac=inc_mac(collected_mac[port]['mac'], i),
                                               port=port,
                                               vlan=collected_mac[port]['vlan'])

    # 3.Verify no errors in ifupdown2 config, apply config, compare running ifupdown2 config vs default config
    await write_reload_check_ifupdown_config(dent_dev, full_config, config['default_interfaces_configfile'])

    # 4.Verify that bridge device added with 4 member ports and expected vlans
    await asyncio.sleep(4)  # Sleep some time for ports to get UP
    await check_member_devices(dev_name, {bridge: dut_ports})
    await check_vlan_members(dev_name, dut_ports, vlans, pvid=pvid)

    # 5.Init interfaces and connect devices
    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': tg_ports[0], 'ip': '1.1.1.2', 'gw': '1.1.1.5', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '2.2.2.2', 'gw': '2.2.2.5', 'plen': 24},
        {'ixp': tg_ports[2], 'ip': '3.3.3.2', 'gw': '3.3.3.5', 'plen': 24},
        {'ixp': tg_ports[3], 'ip': '4.4.4.2', 'gw': '4.4.4.5', 'plen': 24}]
    )
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 6.Setup 1 untagged stream and 3 tagged streams
    streams = {'s1': {
                'type': 'raw',
                'ip_source': dev_groups[tg_ports[0]][0]['name'],
                'ip_destination': [dev_groups[tg_ports[indx]][0]['name'] for indx in range(1, 4)],
                'frame_rate_type': 'line_rate',
                'srcMac': format_mac(dut_ports[0], 1),
                'dstMac': random_mac(),
                'protocol': '802.1Q',
                'rate': 16,
                'skipL3': True}
               }

    streams.update({
        f'vlan_{collected_mac[port]["vlan"]}': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[indx + 1]][0]['name'],
            'frame_rate_type': 'line_rate',
            'srcMac': format_mac(dut_ports[0], collected_mac[port]['vlan']),
            'dstMac': {'type': 'increment',
                       'start': collected_mac[port]['mac'],
                       'step': '00:00:00:00:00:01',
                       'count': num_of_macs},
            'protocol': '802.1Q',
            'vlanID': collected_mac[port]['vlan'],
            'rate': 16,
            'skipL3': True,
        } for indx, port in enumerate(collected_mac)
    })
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=streams)

    # 7.Transmit streams
    await start_and_stop_stream(tgen_dev, traffic_duration)

    # 8.Verify that untagged traffic was flooded, tagged traffic switched to expected port without loss
    stats = await tgen_utils_get_traffic_stats(tgen_dev, stats_type='Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    # 9.Reboot DUT
    await reboot_and_wait(dent_dev)

    # 10.Compare running ifupdown2 config vs default config
    rc, out = await dent_dev.run_cmd(f"ifquery -a -c -i {config['default_interfaces_configfile']}")
    assert not rc, f'Unexpected running configuration \n{out}'

    # 11.Verify that bridge device added with 4 member ports and expected vlans
    await check_member_devices(dev_name, {bridge: dut_ports})
    await check_vlan_members(dev_name, dut_ports, vlans, pvid=pvid)

    # 12.Transmit streams
    await start_and_stop_stream(tgen_dev, traffic_duration)

    # 13.Verify that untagged traffic was flooded, tagged traffic switched to expected port without loss
    stats = await tgen_utils_get_traffic_stats(tgen_dev, stats_type='Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'


async def test_ifupdown2_lacp(testbed, prepare_env):
    """
    Test Name: test_ifupdown2_lacp
    Test Suite: suite_functional_ifupdown2
    Test Overview: Test ifupdown2 with Lag devices
    Test Procedure:
    1. Prepare ifupdown2 environment config
    2. Prepare ifupdown2 config: Add 2 lags with 3 loopbacks, Add 2 bridges with 1 bond and 1 port connected to Ixia
    3. Verify no errors in ifupdown2 config, apply config, compare running ifupdown2 config vs default config
    4. Verify lags, bridges created and members_devices present
    5. Init interfaces and connect devices
    6. Setup bidirectional streams, Transmit streams for a certain duration of time
    7. Verify all traffic is forwarded to each host without packet loss
    8. Reboot Dut
    9. Compare running ifupdown2 config vs default config
    10. Verify lags, bridges created and members_devices present
    11. Transmit streams for a certain duration of time
    12. Verify all traffic is forwarded to each host without packet loss
    """

    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 2)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dev_name = dent_devices[0].host_name
    dent_dev = dent_devices[0]
    tg_ports = tgen_dev.links_dict[dev_name][0]
    dut_ports = tgen_dev.links_dict[dev_name][1]
    traffic_duration = randint(10, 30)
    full_config = ''
    bond1, bond2 = 'bond1', 'bond2'
    bridge1, bridge2 = 'br1', 'br2'

    # 1.Prepare ifupdown2 environment config
    config = {'template_lookuppath': '/etc/network/ifupdown2/templates',
              'addon_syntax_check': 1,
              'default_interfaces_configfile': INTERFACES_FILE
              }
    rc = await prepare_env(dent_dev, config)
    assert not rc, 'Failed to prepare ifupdown2 enviroment config'

    # 2.Prepare ifupdown2 config: Add 2 lags with 3 loopbacks, Add 2 bridges with 1 bond and 1 port connected to Ixia
    full_config += LACP_TEMPLATE.format(bond=bond1,
                                        member_ports=' '.join(dent_dev.links_dict[dev_name][0]))
    full_config += LACP_TEMPLATE.format(bond=bond2,
                                        member_ports=' '.join(dent_dev.links_dict[dev_name][1]))
    full_config += config_bridge(bridge1, [dut_ports[0], bond1])
    full_config += config_bridge(bridge2, [dut_ports[1], bond2])

    # 3.Verify no errors in ifupdown2 config, apply config, compare running ifupdown2 config vs default config
    await write_reload_check_ifupdown_config(dent_dev, full_config, config['default_interfaces_configfile'])

    # 4.Verify lags, bridges created and members_devices present
    device_members = {bond1: dent_dev.links_dict[dev_name][0],
                      bond2: dent_dev.links_dict[dev_name][1],
                      bridge1: [dut_ports[0], bond1],
                      bridge2: [dut_ports[1], bond2]
                      }
    await check_member_devices(dev_name, device_members)

    # 5.Init interfaces and connect devices
    dev_groups = tgen_utils_dev_groups_from_config([
        {'ixp': tg_ports[0], 'ip': '10.1.1.2', 'gw': '10.1.1.1', 'plen': 24},
        {'ixp': tg_ports[1], 'ip': '20.1.1.2', 'gw': '20.1.1.1', 'plen': 24}
    ])
    await tgen_utils_traffic_generator_connect(tgen_dev, tg_ports, dut_ports, dev_groups)

    # 6.Setup bidirectional streams, Transmit streams for a certain duration of time
    s_mac1, s_mac2 = random_mac(), random_mac()
    ip_net1, _ = gen_random_ip_net()
    ip_net2, _ = gen_random_ip_net()

    bidirectional_streams = {
        'bidirectional_stream_1': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[0]][0]['name'],
            'ip_destination': dev_groups[tg_ports[1]][0]['name'],
            'srcMac': s_mac1,
            'dstMac': s_mac2,
            'srcIp': str(ip_net1[1]),
            'dstIp': {'type': 'increment',
                      'start': str(ip_net2[1]),
                      'step':  '0.0.0.1',
                      'count': 100},
            'rate': 100,
            'frame_rate_type': 'line_rate',
        },
        'bidirectional_stream_2': {
            'type': 'raw',
            'ip_source': dev_groups[tg_ports[1]][0]['name'],
            'ip_destination': dev_groups[tg_ports[0]][0]['name'],
            'srcMac': s_mac2,
            'dstMac': s_mac1,
            'srcIp': str(ip_net2[1]),
            'dstIp': {'type': 'increment',
                      'start': str(ip_net1[1]),
                      'step':  '0.0.0.1',
                      'count': 100},
            'rate': 100,
            'frame_rate_type': 'line_rate',
        }
    }
    await tgen_utils_setup_streams(tgen_dev, config_file_name=None, streams=bidirectional_streams)
    await start_and_stop_stream(tgen_dev, traffic_duration)

    # 7.Verify all traffic is forwarded to each host without packet loss
    stats = await tgen_utils_get_traffic_stats(tgen_dev, stats_type='Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'

    # 8.Reboot Dut
    await reboot_and_wait(dent_dev)

    # 9.Compare running ifupdown2 config vs default config
    rc, out = await dent_dev.run_cmd(f"ifquery -a -c -i {config['default_interfaces_configfile']}")
    assert not rc, f'Unexpected running configuration \n{out}'

    # 10.Verify lags, bridges created and members_devices present
    await check_member_devices(dev_name, device_members)

    # 11.Transmit streams for a certain duration of time
    await start_and_stop_stream(tgen_dev, traffic_duration)

    # 12.Verify all traffic is forwarded to each host without packet loss
    stats = await tgen_utils_get_traffic_stats(tgen_dev, stats_type='Flow Statistics')
    for row in stats.Rows:
        loss = tgen_utils_get_loss(row)
        assert loss == 0, f'Expected loss: 0%, actual: {loss}%'
