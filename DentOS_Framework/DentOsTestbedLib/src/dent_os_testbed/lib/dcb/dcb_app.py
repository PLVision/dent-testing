# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/network/dcb/dcb.yaml
#
# DONOT EDIT - generated by diligent bots

import pytest
from dent_os_testbed.lib.test_lib_object import TestLibObject
from dent_os_testbed.lib.dcb.linux.linux_dcb_app_impl import LinuxDcbAppImpl


class DcbApp(TestLibObject):
    """
        dcb [ OPTIONS ] app { COMMAND | help }

        dcb app  {  show  |  flush  }  dev DEV [ default-prio ] [
                 ethtype-prio ] [ stream-port-prio ] [ dgram-port-prio ] [
                 port-prio ] [ dscp-prio ]

        dcb app  {  add  |  del  |  replace  }  dev DEV [ default-prio
                 PRIO-LIST ] [ ethtype-prio ET-MAP ] [ stream-port-prio
                 PORT-MAP ] [ dgram-port-prio PORT-MAP ] [ port-prio PORT-
                 MAP ] [ dscp-prio DSCP-MAP ]

        PRIO-LIST := [ PRIO-LIST ] PRIO
        ET-MAP := [ ET-MAP ] ET-MAPPING
        ET-MAPPING := ET:PRIO
        PORT-MAP := [ PORT-MAP ] PORT-MAPPING
        PORT-MAPPING := PORT:PRIO
        DSCP-MAP := [ DSCP-MAP ] DSCP-MAPPING
        DSCP-MAPPING := { DSCP | all }:PRIO
        ET := { 0x600 .. 0xffff }
        PORT := { 1 .. 65535 }
        DSCP := { 0 .. 63 }
        PRIO := { 0 .. 7 }

    """
    async def _run_command(api, *argv, **kwarg):
        devices = kwarg['input_data']
        result = list()
        for device in devices:
            for device_name in device:
                device_result = {
                    device_name : dict()
                }
                # device lookup
                if 'device_obj' in kwarg:
                    device_obj = kwarg.get('device_obj', None)[device_name]
                else:
                    if device_name not in pytest.testbed.devices_dict:
                        device_result[device_name] = 'No matching device ' + device_name
                        result.append(device_result)
                        return result
                    device_obj = pytest.testbed.devices_dict[device_name]
                commands = ''
                if device_obj.os in ['dentos']:
                    impl_obj = LinuxDcbAppImpl()
                    for command in device[device_name]:
                        commands += impl_obj.format_command(command=api, params=command)
                        commands += '&& '
                    commands = commands[:-3]

                else:
                    device_result[device_name]['rc'] = -1
                    device_result[device_name]['result'] = 'No matching device OS ' + device_obj.os
                    result.append(device_result)
                    return result
                device_result[device_name]['command'] = commands
                try:
                    rc, output = await device_obj.run_cmd(('sudo ' if device_obj.ssh_conn_params.pssh else '') + commands)
                    device_result[device_name]['rc'] = rc
                    device_result[device_name]['result'] = output
                    if 'parse_output' in kwarg:
                        parse_output = impl_obj.parse_output(command=api, output=output, commands=commands)
                        device_result[device_name]['parsed_output'] = parse_output
                except Exception as e:
                    device_result[device_name]['rc'] = -1
                    device_result[device_name]['result'] = str(e)
                result.append(device_result)
        return result

    async def show(*argv, **kwarg):
        """
        Platforms: ['dentos']
        Usage:
        DcbApp.show(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1
                        'dev':'string',
                        'default_prio':'list',
                        'dscp_prio':'list',
                        'ethtype_prio':'list',
                        'port_prio':'list',
                        'stream_port_prio':'list',
                        'dgram_port_prio':'list',
                }],
            }],
        )
        Description:
        dcb app {  show  |  flush  }  dev DEV [ default-prio ] [
                ethtype-prio ] [ stream-port-prio ] [ dgram-port-prio ] [
                port-prio ] [ dscp-prio ]

        """
        return await DcbApp._run_command('show', *argv, **kwarg)

    async def flush(*argv, **kwarg):
        """
        Platforms: ['dentos']
        Usage:
        DcbApp.flush(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1
                        'dev':'string',
                        'default_prio':'list',
                        'dscp_prio':'list',
                        'ethtype_prio':'list',
                        'port_prio':'list',
                        'stream_port_prio':'list',
                        'dgram_port_prio':'list',
                }],
            }],
        )
        Description:
        dcb app {  show  |  flush  }  dev DEV [ default-prio ] [
                ethtype-prio ] [ stream-port-prio ] [ dgram-port-prio ] [
                port-prio ] [ dscp-prio ]

        """
        return await DcbApp._run_command('flush', *argv, **kwarg)

    async def add(*argv, **kwarg):
        """
        Platforms: ['dentos']
        Usage:
        DcbApp.add(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1
                        'dev':'string',
                        'default_prio':'list',
                        'dscp_prio':'list',
                        'ethtype_prio':'list',
                        'port_prio':'list',
                        'stream_port_prio':'list',
                        'dgram_port_prio':'list',
                }],
            }],
        )
        Description:
        dcb app {  add  |  del  |  replace  }  dev DEV [ default-prio
                PRIO-LIST ] [ ethtype-prio ET-MAP ] [ stream-port-prio
                PORT-MAP ] [ dgram-port-prio PORT-MAP ] [ port-prio PORT-
                MAP ] [ dscp-prio DSCP-MAP ]

        """
        return await DcbApp._run_command('add', *argv, **kwarg)

    async def delete(*argv, **kwarg):
        """
        Platforms: ['dentos']
        Usage:
        DcbApp.delete(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1
                        'dev':'string',
                        'default_prio':'list',
                        'dscp_prio':'list',
                        'ethtype_prio':'list',
                        'port_prio':'list',
                        'stream_port_prio':'list',
                        'dgram_port_prio':'list',
                }],
            }],
        )
        Description:
        dcb app {  add  |  del  |  replace  }  dev DEV [ default-prio
                PRIO-LIST ] [ ethtype-prio ET-MAP ] [ stream-port-prio
                PORT-MAP ] [ dgram-port-prio PORT-MAP ] [ port-prio PORT-
                MAP ] [ dscp-prio DSCP-MAP ]

        """
        return await DcbApp._run_command('delete', *argv, **kwarg)

    async def replace(*argv, **kwarg):
        """
        Platforms: ['dentos']
        Usage:
        DcbApp.replace(
            input_data = [{
                # device 1
                'dev1' : [{
                    # command 1
                        'dev':'string',
                        'default_prio':'list',
                        'dscp_prio':'list',
                        'ethtype_prio':'list',
                        'port_prio':'list',
                        'stream_port_prio':'list',
                        'dgram_port_prio':'list',
                }],
            }],
        )
        Description:
        dcb app {  add  |  del  |  replace  }  dev DEV [ default-prio
                PRIO-LIST ] [ ethtype-prio ET-MAP ] [ stream-port-prio
                PORT-MAP ] [ dgram-port-prio PORT-MAP ] [ port-prio PORT-
                MAP ] [ dscp-prio DSCP-MAP ]

        """
        return await DcbApp._run_command('replace', *argv, **kwarg)
