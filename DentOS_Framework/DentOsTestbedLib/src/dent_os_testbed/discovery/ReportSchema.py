# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file dent
#
# DONOT EDIT - generated by diligent bots

import io
import json
import copy
from dent_os_testbed.discovery.Report import (LeafSchemaDict, SchemaList, SchemaDict, Report)
class OspfNeighSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml ospf_neigh
    """
    __schema_slots__ = {
        "address":str,
        "router_id":str,
        "priority":str,
        "state":str,
        "interface":str,

    }
class OspfNeighSchemaList(SchemaList):
    """
    """
    __item_klass__ = OspfNeighSchemaDict
class BgpNeighSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml bgp_neigh
    """
    __schema_slots__ = {
        "neighbor":str,
        "as_":str,
        "up":str,
        "state":str,

    }
class BgpNeighSchemaList(SchemaList):
    """
    """
    __item_klass__ = BgpNeighSchemaDict
class NexthopSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/ip/route.yaml nexthop
    """
    __schema_slots__ = {
        "via":str,
        "dev":str,
        "weight":int,

    }
class NexthopSchemaList(SchemaList):
    """
    """
    __item_klass__ = NexthopSchemaDict
class IpAddressInfoSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/ip/address.yaml ip_address_info
    """
    __schema_slots__ = {
        "family":str,
        "local":str,
        "prefixlen":int,
        "scope":str,
        "label":str,
        "valid_life_time":int,
        "preferred_life_time":int,

    }
class IpAddressInfoSchemaList(SchemaList):
    """
    """
    __item_klass__ = IpAddressInfoSchemaDict
class InterfaceNamesSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml interface_names
    """
    __schema_slots__ = {
        "name":str,

    }
class InterfaceNamesSchemaList(SchemaList):
    """
    """
    __item_klass__ = InterfaceNamesSchemaDict
class InterfaceAddrSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml interface_addr
    """
    __schema_slots__ = {
        "family":str,
        "local":str,
        "prefixlen":int,
        "scope":str,
        "label":str,

    }
class InterfaceAddrSchemaList(SchemaList):
    """
    """
    __item_klass__ = InterfaceAddrSchemaDict
class SfpSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml sfp
    """
    __schema_slots__ = {
        "vendor":str,
        "model":str,
        "serial":str,

    }
class TestbedOspfRoutersSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_ospf_routers
    """
    __schema_slots__ = {
        "address":str,
        "router_id":str,
        "device_id":str,

    }
class TestbedOspfRoutersSchemaList(SchemaList):
    """
    """
    __item_klass__ = TestbedOspfRoutersSchemaDict
class TestbedBgpRoutersSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_bgp_routers
    """
    __schema_slots__ = {
        "router":str,
        "device_id":str,

    }
class TestbedBgpRoutersSchemaList(SchemaList):
    """
    """
    __item_klass__ = TestbedBgpRoutersSchemaDict
class TestbedInterfacesSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_interfaces
    """
    __schema_slots__ = {
        "device_id":str,
        "interface":str,

    }
class TestbedInterfacesSchemaList(SchemaList):
    """
    """
    __item_klass__ = TestbedInterfacesSchemaDict
class SysctlSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/system/os/sysctl.yaml sysctl
    """
    __schema_slots__ = {
        "variable":str,
        "value":str,

    }
class SysctlSchemaList(SchemaList):
    """
    """
    __item_klass__ = SysctlSchemaDict
class DiskFreeSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/system/os/disk.yaml disk_free
    """
    __schema_slots__ = {
        "filesystem":str,
        "size":int,
        "used":int,
        "available":int,
        "use_percentage":int,
        "mounted_on":str,

    }
class DiskFreeSchemaList(SchemaList):
    """
    """
    __item_klass__ = DiskFreeSchemaDict
class ServiceSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/system/os/service.yaml service
    """
    __schema_slots__ = {
        "name":str,
        "loaded":str,
        "active":str,
        "status":str,
        "description":str,

    }
class ServiceSchemaList(SchemaList):
    """
    """
    __item_klass__ = ServiceSchemaDict
class ProcessSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/system/os/process.yaml process
    """
    __schema_slots__ = {
        "pid":int,
        "command":str,
        "elapsed":str,
        "vsz":str,
        "mem":str,
        "time":str,
        "args":str,
        "start_time":str,
        "cpu_usage_user":int,
        "cpu_usage_system":int,
        "cpu_utilization":float,
        "memory_usage":int,
        "memory_utilization":float,

    }
class ProcessSchemaList(SchemaList):
    """
    """
    __item_klass__ = ProcessSchemaDict
class MemoryUsageSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/system/os/memory.yaml memory_usage
    """
    __schema_slots__ = {
        "mem_total":int,
        "mem_free":int,
        "mem_available":int,
        "buffers":int,
        "cached":int,
        "swap_cached":int,
        "active":int,
        "inactive":int,

    }
class CpuUsageSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/system/os/cpu.yaml cpu_usage
    """
    __schema_slots__ = {
        "cpu":int,
        "usr":float,
        "nice":float,
        "sys":float,
        "iowait":float,
        "irq":float,
        "soft":float,
        "steal":float,
        "guest":float,
        "idle":float,

    }
class CpuUsageSchemaList(SchemaList):
    """
    """
    __item_klass__ = CpuUsageSchemaDict
class OspfSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml ospf
    """
    __schema_slots__ = {
        "router_id":str,
        "neighbors":OspfNeighSchemaList,

    }
class OspfSchemaList(SchemaList):
    """
    """
    __item_klass__ = OspfSchemaDict
class BgpSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml bgp
    """
    __schema_slots__ = {
        "as_":int,
        "router":str,
        "neighbors":BgpNeighSchemaList,

    }
class BgpSchemaList(SchemaList):
    """
    """
    __item_klass__ = BgpSchemaDict
class IpTablesSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/iptables/iptables.yaml ip_tables
    """
    __schema_slots__ = {
        "table":str,
        "chain":str,
        "rulenum":int,
        "protocol":str,
        "source":str,
        "destination":str,
        "match":str,
        "target":str,
        "goto":str,
        "iif":str,
        "oif":str,
        "fragment":bool,

    }
class IpTablesSchemaList(SchemaList):
    """
    """
    __item_klass__ = IpTablesSchemaDict
class IpRouteSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/ip/route.yaml ip_route
    """
    __schema_slots__ = {
        "type":str,
        "dst":str,
        "dev":str,
        "protocol":str,
        "scope":str,
        "prefsrc":str,
        "flags":str,
        "tos":int,
        "table":int,
        "metric":int,
        "nexthops":NexthopSchemaList,
        "via":str,
        "weight":int,
        "nhflags":int,
        "mtu":int,
        "advmss":int,
        "rtt":int,
        "rttvar":int,
        "reordering":int,
        "window":int,
        "cwnd":int,
        "ssthresh":int,
        "realms":int,
        "rto_min":str,
        "initcwnd":int,
        "initrwnd":int,
        "quickack":bool,
        "gateway":str,
        "src":str,
        "options":str,

    }
class IpRouteSchemaList(SchemaList):
    """
    """
    __item_klass__ = IpRouteSchemaDict
class IpAddressSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/ip/address.yaml ip_address
    """
    __schema_slots__ = {
        "ifindex":int,
        "ifname":str,
        "flags":str,
        "mtu":int,
        "qdisc":str,
        "operstate":str,
        "group":str,
        "txqlen":int,
        "link_type":str,
        "address":str,
        "broadcast":str,
        "promiscuity":int,
        "min_mtu":int,
        "max_mtu":int,
        "num_tx_queues":int,
        "num_rx_queues":int,
        "gso_max_size":int,
        "gso_max_segs":int,
        "addr_info":IpAddressInfoSchemaList,
        "prefix":str,
        "peer":str,
        "anycast":str,
        "label":str,
        "scope":int,
        "dev":str,
        "options":str,

    }
class IpAddressSchemaList(SchemaList):
    """
    """
    __item_klass__ = IpAddressSchemaDict
class BridgeSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml bridge
    """
    __schema_slots__ = {
        "name":str,
        "interfaces":InterfaceNamesSchemaList,
        "stp":bool,

    }
class BridgeSchemaList(SchemaList):
    """
    """
    __item_klass__ = BridgeSchemaDict
class VlansSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml vlans
    """
    __schema_slots__ = {
        "vlan_id":int,
        "access_ports":InterfaceNamesSchemaList,
        "trunk_ports":InterfaceNamesSchemaList,

    }
class VlansSchemaList(SchemaList):
    """
    """
    __item_klass__ = VlansSchemaDict
class LagsSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml lags
    """
    __schema_slots__ = {
        "name":str,
        "interfaces":InterfaceNamesSchemaList,

    }
class LagsSchemaList(SchemaList):
    """
    """
    __item_klass__ = LagsSchemaDict
class IpLinkSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/ip/link.yaml ip_link
    """
    __schema_slots__ = {
        "ageing_time":int,
        "ifindex":int,
        "ifname":str,
        "flags":str,
        "mtu":int,
        "qdisc":str,
        "operstate":str,
        "linkmode":str,
        "group":str,
        "txqlen":int,
        "link_type":str,
        "address":str,
        "broadcast":str,
        "promiscuity":int,
        "min_mtu":int,
        "max_mtu":int,
        "inet6_addr_gen_mode":str,
        "num_tx_queues":int,
        "num_rx_queues":int,
        "gso_max_size":int,
        "gso_max_segs":int,
        "phys_port_name":str,
        "phys_switch_id":str,
        "device":str,
        "arp":bool,
        "allmulticast":bool,
        "dynamic":bool,
        "multicast":bool,
        "txqueuelen":int,
        "name":str,
        "netns":int,
        "alias":str,
        "vf":int,
        "mac":str,
        "qos":int,
        "vlan":int,
        "rate":int,
        "max_tx_rate":int,
        "min_tx_rate":int,
        "spoofchk":int,
        "state":str,
        "master":str,
        "nomaster":bool,
        "options":str,

    }
class IpLinkSchemaList(SchemaList):
    """
    """
    __item_klass__ = IpLinkSchemaDict
class InterfacesSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml interfaces
    """
    __schema_slots__ = {
        "name":str,
        "speed":int,
        "media":str,
        "configured_state":str,
        "peer_device_id":str,
        "peer_interface":str,
        "operstate":str,
        "flags":list,
        "mtu":int,
        "index":int,
        "qdisc":str,
        "group":str,
        "txqlen":int,
        "link_type":str,
        "address":str,
        "broadcast":str,
        "sfp":SfpSchemaDict,
        "addr_info":InterfaceAddrSchemaList,

    }
class InterfacesSchemaList(SchemaList):
    """
    """
    __item_klass__ = InterfacesSchemaDict
class LldpSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/lldp/lldp.yaml lldp
    """
    __schema_slots__ = {
        "interface":str,
        "options":str,
        "remote_host":str,
        "remote_interface":str,

    }
class LldpSchemaList(SchemaList):
    """
    """
    __item_klass__ = LldpSchemaDict
class OnlpSfpInfoSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/onlp/onlpdump.yaml onlp_sfp_info
    """
    __schema_slots__ = {
        "port":int,
        "type":str,
        "media":str,
        "status":str,
        "len":str,
        "vendor":str,
        "model":str,
        "serial_number":str,

    }
class OnlpSfpInfoSchemaList(SchemaList):
    """
    """
    __item_klass__ = OnlpSfpInfoSchemaDict
class OnlpSystemInfoSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/onlp/onlpdump.yaml onlp_system_info
    """
    __schema_slots__ = {
        "product_name":str,
        "serial_number":str,
        "mac":str,
        "mac_range":str,
        "manufacturer":str,
        "manufacturer_date":str,
        "vendor":str,
        "platform_name":str,
        "device_version":str,
        "label_revision":str,
        "country_code":str,
        "diag_version":str,
        "service_tag":str,
        "onie_version":str,

    }
class PoectlSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/poe/peoctl.yaml poectl
    """
    __schema_slots__ = {
        "port":str,
        "cmd_options":str,
        "status":str,
        "priority":str,
        "power":str,
        "pd_type":str,
        "current":str,
        "state":str,
        "voltage":str,
        "pd_class":str,
        "allocated_power":str,
        "error_str":str,

    }
class PoectlSchemaList(SchemaList):
    """
    """
    __item_klass__ = PoectlSchemaDict
class FruItemSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/platform.yaml fru_item
    """
    __schema_slots__ = {
        "name":str,
        "model":str,
        "serial":str,

    }
class FruItemSchemaList(SchemaList):
    """
    """
    __item_klass__ = FruItemSchemaDict
class PartitionItemSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/platform.yaml partition_item
    """
    __schema_slots__ = {
        "mount":str,
        "device":str,
        "size":int,
        "free":int,
        "opts":str,

    }
class PartitionItemSchemaList(SchemaList):
    """
    """
    __item_klass__ = PartitionItemSchemaDict
class TestbedOspfSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_ospf
    """
    __schema_slots__ = {
        "routers":TestbedOspfRoutersSchemaList,

    }
class TestbedBgpSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_bgp
    """
    __schema_slots__ = {
        "routers":TestbedBgpRoutersSchemaList,

    }
class TestbedVlansSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_vlans
    """
    __schema_slots__ = {
        "vlan_id":str,
        "access_port":TestbedInterfacesSchemaList,
        "trunk_port":TestbedInterfacesSchemaList,

    }
class TestbedVlansSchemaList(SchemaList):
    """
    """
    __item_klass__ = TestbedVlansSchemaDict
class OperatingSystemSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/system/system.yaml operating_system
    """
    __schema_slots__ = {
        "cpu":CpuUsageSchemaList,
        "memory":MemoryUsageSchemaDict,
        "processes":ProcessSchemaList,
        "services":ServiceSchemaList,
        "disk":DiskFreeSchemaList,
        "sysctl":SysctlSchemaList,

    }
class L3SchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml l3
    """
    __schema_slots__ = {
        "management_ip":str,
        "addresses":IpAddressSchemaList,
        "routes":IpRouteSchemaList,
        "iptables":IpTablesSchemaList,
        "acls":LeafSchemaDict,
        "bgp":BgpSchemaList,
        "ospf":OspfSchemaList,

    }
class L2SchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml l2
    """
    __schema_slots__ = {
        "vlans":VlansSchemaList,
        "bridges":BridgeSchemaList,

    }
class L1SchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml l1
    """
    __schema_slots__ = {
        "management_mac":str,
        "interfaces":InterfacesSchemaList,
        "links":IpLinkSchemaList,
        "lags":LagsSchemaList,

    }
class LldpSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/platform.yaml lldp
    """
    __schema_slots__ = {
        "interfaces":LldpSchemaList,

    }
class OnlpSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/platform.yaml onlp
    """
    __schema_slots__ = {
        "system_information":OnlpSystemInfoSchemaDict,
        "sfps":OnlpSfpInfoSchemaList,

    }
class PoeSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/platform.yaml poe
    """
    __schema_slots__ = {
        "ports":PoectlSchemaList,

    }
class FruSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/platform.yaml fru
    """
    __schema_slots__ = {
        "fans":FruItemSchemaList,
        "psus":FruItemSchemaList,
        "serial":FruItemSchemaList,

    }
class BaseboardSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/platform.yaml baseboard
    """
    __schema_slots__ = {
        "platform":str,
        "serial":str,
        "cpu_type":str,
        "cpu_speed":int,
        "cpu_core_count":int,
        "memory_total":int,
        "memory_free":int,
        "partitions":PartitionItemSchemaList,

    }
class TrafficGenSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/traffic/traffic.yaml traffic_gen
    """
    __schema_slots__ = {
        "client_addr":str,
        "config_file_name":str,
        "protocols":str,
        "traffic_names":str,
        "ports":str,
        "src_ip":str,
        "dst_ip":str,

    }
class TestbedL3SchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_l3
    """
    __schema_slots__ = {
        "bgp":TestbedBgpSchemaDict,
        "ospf":TestbedOspfSchemaDict,

    }
class TestbedL2SchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_l2
    """
    __schema_slots__ = {
        "vlans":TestbedVlansSchemaList,

    }
class DeviceSystemSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/system/system.yaml device_system
    """
    __schema_slots__ = {
        "os":OperatingSystemSchemaDict,

    }
class DeviceNetworkSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/network/network.yaml device_network
    """
    __schema_slots__ = {
        "layer1":L1SchemaDict,
        "layer2":L2SchemaDict,
        "layer3":L3SchemaDict,

    }
class PlatformSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/platform/platform.yaml platform
    """
    __schema_slots__ = {
        "baseboard":BaseboardSchemaDict,
        "software":LeafSchemaDict,
        "fru":FruSchemaDict,
        "poe":PoeSchemaDict,
        "onlp":OnlpSchemaDict,
        "lldp":LldpSchemaDict,

    }
class TrafficGeneratorsSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/traffic/traffic.yaml traffic_generators
    """
    __schema_slots__ = {
        "generator":TrafficGenSchemaDict,

    }
class TestbedNetworkSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/testbed/testbed.yaml testbed_network
    """
    __schema_slots__ = {
        "layer2":TestbedL2SchemaDict,
        "layer3":TestbedL3SchemaDict,

    }
class InfrastructureSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/base/base.yaml infrastructure
    """
    __schema_slots__ = {
        "device_id":str,
        "network":DeviceNetworkSchemaDict,

    }
class InfrastructureSchemaList(SchemaList):
    """
    """
    __item_klass__ = InfrastructureSchemaDict
class DutsSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/base/base.yaml duts
    """
    __schema_slots__ = {
        "device_id":str,
        "platform":PlatformSchemaDict,
        "network":DeviceNetworkSchemaDict,
        "system":DeviceSystemSchemaDict,

    }
class DutsSchemaList(SchemaList):
    """
    """
    __item_klass__ = DutsSchemaDict
class ReportSchemaDict(SchemaDict):
    """
    Refer ./gen/model/dent/base/base.yaml base
    """
    __schema_slots__ = {
        "attributes":LeafSchemaDict,
        "duts":DutsSchemaList,
        "infrastructure":InfrastructureSchemaList,
        "network":TestbedNetworkSchemaDict,
        "traffic_genertors":TrafficGeneratorsSchemaDict,

    }
class ReportSchema(Report):
    """
    """
    def __init__(self, jsonData):
        self.data = ReportSchemaDict(jsonData)

    def clone(self, jsonData):
        return ReportSchema(jsonData)

    def fromPath(path):
        with io.open(path, "rt") as fd:
            data = json.load(fd)
        return ReportSchema(data)
