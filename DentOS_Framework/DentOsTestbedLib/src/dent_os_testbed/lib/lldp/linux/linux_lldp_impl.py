from dent_os_testbed.lib.lldp.linux.linux_lldp import LinuxLldp


class LinuxLldpImpl(LinuxLldp):
    """
    LLDP module

    """

    def format_show(self, command, *argv, **kwarg):
        """
        Usage:   lldpctl [OPTIONS ...] [COMMAND ...]
        Version: lldpd 2020-09-23
        -d          Enable more debugging information.
        -u socket   Specify the Unix-domain socket used for communication with lldpd(8).
        -f format   Choose output format (plain, keyvalue, json, json0, xml).
        see manual page lldpcli(8) for more information

        """
        params = kwarg['params']
        if params.get('dut_discovery', False):
            params['cmd_options'] = '-f json'
        if 'lldpctl' in kwarg['params']:
            cmd = 'lldpctl{} {} '.format(params.get('cmd_options', ''), command)
        else:
            cmd = 'lldpcli{} {} '.format(params.get('cmd_options', ''), command)
        if 'neighbors' in params and params['neighbors']:
            cmd += 'neighbors '
        if 'statistics' in params and params['statistics']:
            cmd += 'statistics '
        if 'ports' in params and params['ports']:
            cmd += 'ports'
        if 'interface' in kwarg['params']:
            cmd += ' {} '.format(kwarg['params']['interface'])
        return cmd

    def parse_show(self, command, output, *argv, **kwarg):
        lines = output.strip().split('\n')
        lines = lines[2:-2]
        lldp_dict = {}
        for line in lines:
            key_value_pair = line.split(':')
            if len(key_value_pair) != 2:
                continue
            key = key_value_pair[0].strip()
            value = key_value_pair[1].strip()
            lldp_dict[key] = value
        return (lldp_dict)

    # def parse_show(self, command, output, *argv, **kwarg):
    #     interfaces = []
    #     try:
    #         parsed_out = json.loads(output)
    #         for interface in parsed_out['lldp']['interface']:
    #             for port, data in interface.items():
    #                 item = {'interface': port, 'remote_interface': data['port']['id']['value']}
    #                 for chassis in data['chassis']:
    #                     item['remote_host'] = chassis
    #                 interfaces.append(item)
    #     except Exception:
    #         return []
    #     return interfaces

    def format_set(self, command, *argv, **kwarg):
        """
        Usage:   lldpcli [OPTIONS ...] [COMMAND ...]
        Version: lldpd 2020-09-23
        -d          Enable more debugging information.
        -u socket   Specify the Unix-domain socket used for communication with lldpd(8).
        -f format   Choose output format (plain, keyvalue, json, json0, xml).
        see manual page lldpcli(8) for more information

        """
        cmd = 'lldpcli {} '.format(command)
        # TODO: Implement me

        return cmd

    def format_configure(self, command, *argv, **kwarg):
        """
        Usage:   lldpcli [OPTIONS ...] [COMMAND ...]
        Version: lldpd 2020-09-23
        -d          Enable more debugging information.
        -u socket   Specify the Unix-domain socket used for communication with lldpd(8).
        -f format   Choose output format (plain, keyvalue, json, json0, xml).
        see manual page lldpcli(8) for more information

        """
        params = kwarg['params']
        cmd = 'lldpcli {} '.format(command)
        # custom code here
        if 'device' in params:
            cmd += 'ports {} '.format((params['device']))
        if 'lldp' in params and params['lldp']:
            cmd += 'lldp '
        if 'status' in params:
            cmd += 'status {} '.format((params['status']))
        if 'tx-interval' in params:
            cmd += 'tx-interval {} '.format((params['tx-interval']))
        return cmd

    def parse_set(self, command, output, *argv, **kwarg):
        """
        Usage:   lldpcli [OPTIONS ...] [COMMAND ...]
        Version: lldpd 2020-09-23
        -d          Enable more debugging information.
        -u socket   Specify the Unix-domain socket used for communication with lldpd(8).
        -f format   Choose output format (plain, keyvalue, json, json0, xml).
        see manual page lldpcli(8) for more information

        """
        cmd = 'lldpcli {} '.format(command)
        # TODO: Implement me

        return cmd
