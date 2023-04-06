from dent_os_testbed.constants import DEFAULT_LOGGER
from dent_os_testbed.lib.ip.ip_address import IpAddress
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.lib.ip.ip_route import IpRoute
from dent_os_testbed.lib.os.recoverable_sysctl import RecoverableSysctl
from dent_os_testbed.lib.tc.tc_qdisc import TcQdisc
from dent_os_testbed.logger.Logger import AppLogger
from dent_os_testbed.lib.devlink.devlink_port import DevlinkPort


async def cleanup_qdiscs(dev):
    """
    Removes all non-default qdiscs created during test.
    Can be used separately or by using `cleanup_qdiscs` fixture.
    """
    logger = AppLogger(DEFAULT_LOGGER)
    logger.info("Clearing TC")
    out = await TcQdisc.show(
        input_data=[{dev.host_name: [{"options": "-j"}]}],
        parse_output=True
    )
    qdiscs_info = out[0][dev.host_name]["parsed_output"]
    for qdisc_obj in qdiscs_info:
        if qdisc_obj.get("root"):
            await TcQdisc.delete(
                input_data=[{dev.host_name: [{"dev": qdisc_obj["dev"], "root": True}]}]
            )
            continue
        if qdisc_obj["kind"] != "noqueue":
            await TcQdisc.delete(
                input_data=[{dev.host_name: [{"dev": qdisc_obj["dev"], "direction": qdisc_obj["kind"]}]}]
            )


async def cleanup_bridges(dev):
    """
    Removes all bridges created during test.
    Can be used separately or by using `cleanup_bridges` fixture.
    """
    logger = AppLogger(DEFAULT_LOGGER)
    logger.info("Clearing bridges")
    out = await IpLink.show(
        input_data=[{dev.host_name: [{"link_type": "bridge", "cmd_options": "-j"}]}],
        parse_output=True
    )
    bridges_info = out[0][dev.host_name]["parsed_output"]
    if bridges_info:
        await IpLink.delete(input_data=[{dev.host_name: [
            {"device": bridge_obj["ifname"]} for bridge_obj in bridges_info]}
        ])


async def cleanup_vrfs(dev):
    """
    Removes all VRFs created during test.
    Can be used separately or by using `cleanup_vrfs` fixture.
    """
    logger = AppLogger(DEFAULT_LOGGER)
    logger.info("Deleting VRFs")
    out = await IpLink.show(
        input_data=[{dev.host_name: [{"link_type": "vrf",  "cmd_options": "-j"}]}],
        parse_output=True
    )
    vrfs_info = out[0][dev.host_name]["parsed_output"]
    if all(vrfs_info):
        await IpLink.delete(input_data=[{dev.host_name: [
            {"device": vrf_obj["ifname"]} for vrf_obj in vrfs_info
        ]}])


async def cleanup_ip_addrs(dev, tgen_dev):
    """
    Removes all IP addresses configured during test.
    Can be used separately or by using `cleanup_addrs` fixture.
    """
    logger = AppLogger(DEFAULT_LOGGER)
    logger.info("Deleting IP addresses from interfaces")
    ports = tgen_dev.links_dict[dev.host_name][1]
    await IpAddress.flush(input_data=[{dev.host_name: [{"dev": port} for port in ports]}])


async def get_initial_routes(dev):
    """Gets routes defined before test. Needed to cleanup routes configured during the test"""
    out = await IpRoute.show(
        input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
        parse_output=True
    )
    return out[0][dev.host_name]["parsed_output"]


async def cleanup_routes(dev, initial_routes):
    """
    Removes all IP routes configured during test.
    Can be used separately or by using `cleanup_routes` fixture.
    """
    logger = AppLogger(DEFAULT_LOGGER)
    logger.info("Deleting routes")
    out = await IpRoute.show(
        input_data=[{dev.host_name: [{"cmd_options": "-j"}]}],
        parse_output=True
    )
    new_routes = out[0][dev.host_name]["parsed_output"]
    if new_routes != initial_routes:
        await IpRoute.delete(input_data=[{dev.host_name: [
            {"dev": route["dev"], "dst": route["dst"]}
            for route in new_routes if route not in initial_routes
        ]}])


async def cleanup_sysctl():
    """
    Restores all sysctl values changed during test.
    Can be used separately or by using `cleanup_sysctl` fixture.
    """
    logger = AppLogger(DEFAULT_LOGGER)
    logger.info("Restoring sysctl values")
    await RecoverableSysctl.recover()


async def cleanup_kbyte_per_sec_rate_value(dev, all_values=False, bc=False, unk_uc=False, unreg_mc=False):
    """
    Restore values changed during test viz:
        - all kbyte_per_sec_rate values
        - bc_kbyte_per_sec_rate values
        - unk_uc_kbyte_per_sec_rate
        - unreg_mc_kbyte_per_sec_rate
    Can be used separately or by using `cleanup_kbyte_per_sec_rate_value` fixture.
    """
    logger = AppLogger(DEFAULT_LOGGER)
    logger.info("Restoring kbyte_per_sec_rate values")
    out = await DevlinkPort.show(
        input_data=[{dev.host_name: [{"options": "-j"}]}],
        parse_output=True)
    devlink_entries = out[0][dev.host_name]["parsed_output"]

    # restoring kbyte_per_sec_rate all values
    if all_values:
        input_data = ({dev.host_name: [
            {"dev": f"{device}", "name": f"{item['name']}", "value": "0", "cmode": "runtime"}]}
            for device in devlink_entries['param']
            for item in devlink_entries['param'][device]
        )
        await DevlinkPort.set(input_data=input_data)

    # restoring bc_kbyte_per_sec_rate values
    if bc:
        input_data = ({dev.host_name: [
            {"dev": f"{device}", "name": "bc_kbyte_per_sec_rate values", "value": "0", "cmode": "runtime"}]}
            for device in devlink_entries['param']
        )
        await DevlinkPort.set(input_data=input_data)

    # restoring unk_uc_kbyte_per_sec_rate values
    if unk_uc:
        input_data = ({dev.host_name: [
            {"dev": f"{device}", "name": "unk_uc_kbyte_per_sec_rate", "value": "0", "cmode": "runtime"}]}
            for device in devlink_entries['param']
        )
        await DevlinkPort.set(input_data=input_data)

    # restoring unreg_mc_kbyte_per_sec_rate values
    if unreg_mc:
        input_data = ({dev.host_name: [
            {"dev": f"{device}", "name": "unreg_mc_kbyte_per_sec_rate", "value": "0", "cmode": "runtime"}]}
            for device in devlink_entries['param']
        )
        await DevlinkPort.set(input_data=input_data)


async def cleanup_bonds(dev):
    """
    Removes all bonds created during test.
    Can be used separately or by using `cleanup_bonds` fixture.
    """
    logger = AppLogger(DEFAULT_LOGGER)
    logger.info("Deleting bonds")
    out = await IpLink.show(
        input_data=[{dev.host_name: [{"cmd_options": "-j -d"}]}],
        parse_output=True
    )
    bonds_info = out[0][dev.host_name]["parsed_output"]
    for name in bonds_info:
        if name.get('linkinfo', {}).get('info_kind') == 'bond':
            await IpLink.delete(input_data=[{dev.host_name: [
                 {"device": f"{name['ifname']}"}]}])
