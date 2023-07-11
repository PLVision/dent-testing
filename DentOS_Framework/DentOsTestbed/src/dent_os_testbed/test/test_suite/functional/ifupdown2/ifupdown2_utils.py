import time
import asyncio
import re

from random import randint
from ipaddress import IPv4Network

from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_start_traffic,
    tgen_utils_stop_traffic,
    tgen_utils_clear_traffic_stats,
)

IFUPDOWN_CONF = '/etc/network/ifupdown2/ifupdown2.conf'
IFUPDOWN_BACKUP = '/etc/network/ifupdown2/ifupdown2.bak'
INTERFACES_FILE = '/etc/network/interfaces.d/cfg-file-1'
IPV4_TEMPLATE = \
    """

    auto {name}
    iface {name} inet {inet}
        address {address}
    """

ECMP_TEMPLATE = \
    """

    up ip route add {net} {nexthops}
    """

BRIDGE_TEMPLATE = \
    """

    auto {bridge}
    iface {bridge} inet static
        bridge-ports {ports}
    """

FDB_TEMPLATE = \
    """

            up bridge fdb add {mac} dev {port} master static vlan {vlan}
    """

LACP_TEMPLATE = \
    """

    auto {bond}
    iface {bond} inet static
        bond-slaves {member_ports}
        bond-mode 802.3ad
    """


def config_bridge(bridge, ports, vlan_aware=False, pvid=None, vlans=None):
    """
    Setup ifupdown2 config for bridge device
    Args:
        bridge (str): Bridge device name
        ports (list): Bridge member ports
        vlan_aware (bool): Sets bridge to vlan-aware
        pvid (int): Bridge pvid to set
        vlans (list): Bridge vlans to set
    Returns:
        Ifupdown2 bridge config in string representation

    """
    result = BRIDGE_TEMPLATE.format(bridge=bridge, ports=' '.join(ports))
    if vlan_aware:
        result += f'{" " * 4}bridge-vlan-aware yes\n'
    if pvid:
        result += f'{" " * 8}bridge-pvid {pvid}\n'
    if vlans:
        result += f'{" " * 8}bridge-vids {" ".join(vlans)}\n'
    return result


def random_mac():
    return ':'.join(['02'] + [f'{randint(0, 255):02x}' for _ in range(5)])


def conf_ecmp(route, nexthops):
    """
    Setup ifupdown2 config for ecmp route
    Args:
        route (str): Ipv4 route to set as ecmp
        nexthops (list): List of nexthops
    Returns:
        Ifupdown2 ecmp config in string representation
    """
    nexthops_str = ' '.join('nexthop via ' + str(neigh) for neigh in nexthops)
    return ECMP_TEMPLATE.format(net=route, nexthops=nexthops_str)


def gen_random_ip_net(multicast=False):
    """
    Generate random ip network with prefix /8-24
    Args:
        multicast (bool): If True generates multicast route
    Returns:
        IPv4Network object and maximum available host's in network
    """
    first_octet = randint(224, 239) if multicast else randint(10, 200)
    ip = f'{first_octet}.{randint(1, 250)}.{randint(1, 250)}.{randint(1, 250)}/{randint(8, 24)}'
    net = IPv4Network(ip, strict=False)
    return IPv4Network(net.with_prefixlen, strict=True), randint(10, 2**(32 - net.prefixlen))


async def reboot_and_wait(dent_dev):
    """
    Reboot DUT and wait for it to come back
    Args:
        dent_dev (str): Dut name
    """
    await dent_dev.reboot()
    start = time.time()
    while time.time() < start + 300:
        await asyncio.sleep(15)
        device_up = await dent_dev.is_connected()
        if device_up:
            break
    assert device_up, f'Verify that device: {dent_dev.host_name} is up!\n'

    # DUE to issue with ports, run onlpdump
    rc, _ = await dent_dev.run_cmd('/lib/platform-config/current/onl/bin/onlpdump', sudo=True)
    assert not rc, f'Failed to run onlpdump {rc}'


async def write_reload_check_ifupdown_config(dent_dev, config_to_wtite, default_interfaces_configfile):
    """
    Write, Reload and check ifupdown2 config
    Args:
        dent_dev (obj): Dut device object
        config_to_wtite (str): String of ifupdown2 config to write
        default_interfaces_configfile (str): File patch where config will be written to
    """

    # Write desirable ifupdwon2 config to a default_interfaces_configfile
    rc, _ = await dent_dev.run_cmd(f"echo -e '{config_to_wtite}' >> {default_interfaces_configfile}")
    assert not rc, f'Failed to write ifupdown2 config to a {default_interfaces_configfile}'

    # Verify (ifquery) no errors in configuration file
    rc, out = await dent_dev.run_cmd(f'ifquery -a -i {default_interfaces_configfile}')
    assert 'error' not in out.strip(), f'Error spotted in output of ifquery cmd {out.strip()}'

    # Apply (ifreload) ifupdown configuration
    rc, out = await dent_dev.run_cmd('ifreload -a -v')
    assert not rc, f'Failed to reload ifupdown2 config.\n{out}'

    # Check (ifquery --check) running vs actual configuration
    rc, out = await dent_dev.run_cmd(f'ifquery -a -c -i {default_interfaces_configfile}')
    assert not rc, f'Unexpected running configuration \n{out}'


async def verify_ip_address_routes(dev_name, address_map, ecmp_route):
    """
    Verify ip addresses asigned, routes added and ecmp route offloaded
    Args:
        dev_name (str): Dut name
        address_map (list): Address map list
        ecmp_route (str): Ipv4 route addresses used as ECMP
    """
    out = await IpRoute.show(input_data=[{dev_name: [{'cmd_options': '-j -4'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], 'Failed to get routes'
    routes = out[0][dev_name]['parsed_output']

    out = await IpAddress.show(input_data=[{dev_name: [{'cmd_options': '-j -4'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], 'Failed to get IPv4 addresses'
    ip_addrs = out[0][dev_name]['parsed_output']

    for port, _, ip, _, plen in address_map:
        for ip_addr in ip_addrs:
            if port == ip_addr['ifname']:
                assert f'{ip}/{plen}' == f'{ip_addr["addr_info"][0]["local"]}/{ip_addr["addr_info"][0]["prefixlen"]}', \
                    f'{ip}/{plen} != {ip_addr["addr_info"][0]["local"]}/{ip_addr["addr_info"][0]["prefixlen"]}'
        for ro in routes:
            try:
                if ro['dev'] == port:
                    assert str(IPv4Network(f'{ip}/{plen}', strict=False)) == ro['dst'], \
                        f'Route not found {str(IPv4Network(f"{ip}/{plen}", strict=False))}'
            except KeyError:
                pass
            if ro['dst'] == str(ecmp_route):
                assert 'rt_offload' in ro['flags'], f'Ecmp route {ecmp_route} is not offloaded'


async def start_and_stop_stream(tgen_dev, traffic_duration, sleep_time=15):
    """
    Start traffic for a traffic duration and stop it
    Args:
        tgen_dev (obj): Traffic Genearotor object
        traffic_duration (int): Time duration for sending traffic
        sleep_time (int): Time to sleep after traffic sent (for stats stabilization)
    """
    await tgen_utils_clear_traffic_stats(tgen_dev)
    await tgen_utils_start_traffic(tgen_dev)
    await asyncio.sleep(traffic_duration)
    await tgen_utils_stop_traffic(tgen_dev)
    await asyncio.sleep(sleep_time)


def format_mac(port, vlan, offset=0):
    """
    Format Mac address based on port name and vlan
    Args:
        port (str): Dut port name
        vlan (int): Vlan id
        offset (int): Mac address offset
    Returns:
        Formated Mac address
    """
    reg_exp = re.compile(r'(\d+)$')
    port, vlan = (i if isinstance(i, int) else int(reg_exp.search(i).groups()[0]) for i in [port, vlan])
    mac_int = port * 0x100000000 + vlan * 0x10000 + offset
    mac_str = '{:012X}'.format(mac_int)
    return ':'.join(x + y for x, y in zip(mac_str[::2], mac_str[1::2]))


def inc_mac(mac, offset):
    """
    Increment Mac address
    Args:
        mac (str): Mac address
        offset (int): Mac address offset
    Returns:
        Incremented Mac address
    """
    mac_hex = '{:012X}'.format(int(mac.replace(':', ''), 16) + offset)
    return ':'.join(x+y for x, y in zip(mac_hex[::2], mac_hex[1::2]))


async def check_vlan_members(dev_name, dut_ports, vlans, pvid=1):
    """
    Check bridge members vlans
    Args:
        dev_name (str): Dut name
        dut_ports (list): Dut ports
        vlans (list): List of vlans to check
        pvid (int): Expected pvid to check
    """
    out = await BridgeVlan.show(input_data=[{dev_name: [{'cmd_options': '-j'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], f'Failed show bridge vlans.\n{out}'
    parsed = out[0][dev_name]['parsed_output']

    for p_vlans in parsed:
        if p_vlans['ifname'] in dut_ports:
            for vlan in p_vlans['vlans']:
                if vlan['vlan'] == pvid:
                    assert vlan['flags'] == ['PVID', 'Egress Untagged'], f'Unexpected vlan flags {vlan["flags"]}'
                assert vlan['vlan'] in vlans + [pvid], f'Expected vlan {vlan["vlan"]} not in {vlans + [pvid]}'


async def check_member_devices(dev_name, device_members, status='UP'):
    """
    Check device and members status
    Args:
        dev_name (str): Dut name
        device_members (dict): Dict with mapping of device and its members to check
        status (str): Expected status to check
    """
    out = await IpLink.show(input_data=[{dev_name: [{'cmd_options': '-j'}]}], parse_output=True)
    assert not out[0][dev_name]['rc'], 'Failed to get port info'
    parsed = out[0][dev_name]['parsed_output']

    for dev, members in device_members.items():
        out = await IpLink.show(input_data=[{dev_name: [{'device': dev, 'cmd_options': '-j'}]}], parse_output=True)
        assert not out[0][dev_name]['rc'], 'Failed to get port info'
        parsed = out[0][dev_name]['parsed_output']

        assert parsed[0]['ifname'] == dev and parsed[0]['operstate'] == status, f'Unexpected status for device {dev}'

        if members:
            out = await IpLink.show(input_data=[{dev_name: [{'device': dev, 'master': '', 'cmd_options': '-j'}]}], parse_output=True)
            assert not out[0][dev_name]['rc'], 'Failed to get member ports info'
            parsed = out[0][dev_name]['parsed_output']
            for link in parsed:
                assert link['ifname'] in members and link['operstate'] == status, \
                    f'Unexpected member port {link["ifname"]} or state {link["operstate"]}'
