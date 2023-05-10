from dent_os_testbed.lib.lldp.lldp import Lldp


async def verify_lldp_pkt_count(out, device_host_name, exp_count, port):
    out = await Lldp.show(
        input_data=[{device_host_name: [
            {'interface': port, 'statistics': True, 'ports': True}]}], parse_output=True)
    assert out[0][device_host_name]['rc'] == 0, f'Failed to show LLPD statistics.\n{out}'
    lldp_statistics = out[0][device_host_name]['parsed_output']
    err_msg = f'Failed: expected count of LLDP packets: {exp_count}, transmitted: {lldp_statistics["Transmitted"]}.'
    assert int(lldp_statistics['Transmitted']) == exp_count, err_msg


async def set_default_tx_interval(out, device_host_name):
    out = await Lldp.configure(
        input_data=[{device_host_name: [{'lldp': True, 'tx-interval': 30}]}])
    assert out[0][device_host_name]['rc'] == 0, f'Failed to configure default tx-interval.\n{out}'


async def start_or_kill_lldp_service(dent_dev, start=False, kill=False):
    if start:
        rc, out = await dent_dev.run_cmd('lldpd -cefs')
        assert rc == 0, f"Failed to start 'lldp service'.\n{out}"
    if kill:
        rc, out = await dent_dev.run_cmd('killall lldpd')
        assert rc == 0, f"Failed to start 'kill lldp service'\n{out}."
