from dent_os_testbed.lib.devlink.devlink_port import DevlinkPort


async def devlink_rate_value(dev, name, value, cmode=False, device_host_name=True,
                             set=False, verify=False):
    if set:
        out = await DevlinkPort.set(input_data=[{device_host_name: [
            {'dev': dev, 'name': name, 'value': value, 'cmode': cmode}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Failed to set rate value '{value}'.\n{out}"
    if verify:
        out = await DevlinkPort.show(input_data=[{device_host_name: [
            {'options': '-j', 'dev': dev, 'name': name}]}], parse_output=True)
        err_msg = f"Failed to execute the command 'DevlinkPort.show'.\n{out}"
        assert out[0][device_host_name]['rc'] == 0, err_msg
        devlink_info = out[0][device_host_name]['parsed_output']
        kbyte_value = devlink_info['param'][dev][0]['values'][0]['value']
        assert kbyte_value == value, f"Verify that storm control rate configured is '{value}' kbps.\n"
