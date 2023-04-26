import math

from dent_os_testbed.lib.devlink.devlink_port import DevlinkPort
from dent_os_testbed.lib.tc.tc_filter import TcFilter


async def devlink_rate_value(dev, name, value, cmode=False, device_host_name=True, set=False, verify=False):
    if set:
        out = await DevlinkPort.set(input_data=[{device_host_name: [
            {'dev': dev, 'name': name, 'value': value, 'cmode': cmode}]}])
        assert out[0][device_host_name]['rc'] == 0, f"Failed to set rate value '{value}'.\n{out}"
    if verify:
        out = await DevlinkPort.show(input_data=[{device_host_name: [
            {'options': '-j', 'dev': dev, 'name': name}]}], parse_output=True)
        assert out[0][device_host_name]['rc'] == 0, f"Failed to execute the command 'DevlinkPort.show'.\n{out}"
        devlink_info = out[0][device_host_name]['parsed_output']
        kbyte_value = devlink_info['param'][dev][0]['values'][0]['value']
        assert kbyte_value == value, f"Verify that storm control rate configured is '{value}' kbps.\n"


async def verify_expected_rx_rate(kbyte_value, stats, rx_ports, deviation=0.10):
    """
    Verify expected rx_rate in bytes on ports
    Args:
        kbyte_value (int): Kbyte per sec rate
        stats (stats_object): Output of tgen_utils_get_traffic_stats
        rx_ports (list): list of Rx ports which rate should be verified
        deviation (int): Permissible deviation percentage
    """
    collected = {row['Port Name']:
                 {'tx_rate': row['Bytes Tx. Rate'], 'rx_rate': row['Bytes Rx. Rate']} for row in stats.Rows}
    exp_rate = kbyte_value*1000
    for port in rx_ports:
        rx_name = port.split('_')[0]
        res = math.isclose(exp_rate, float(collected[rx_name]['rx_rate']), rel_tol=deviation)
        assert res, 'Verify the rate is limited by storm control.'


async def tc_filter_add(dev, vlan_id, src_mac, dst_mac, rate, burst, device_host_name=True):
    out = await TcFilter.add(
            input_data=[
                {
                    device_host_name: [
                        {
                            'dev': dev,
                            'direction': 'ingress',
                            'protocol': '0x8100',
                            'filtertype': {
                                'skip_sw': '',
                                'vlan_id': vlan_id,
                                'src_mac': src_mac,
                                'dst_mac': dst_mac,
                            },
                            'action': {
                                'trap': '',
                                'police': {
                                    'rate': rate,
                                    'burst': burst,
                                    'conform-exceed': '',
                                    'drop': '',
                                }
                            },
                        }
                    ]
                }
            ]
        )
    assert out[0][device_host_name]['rc'] == 0, f'Failed to create tc rules.\n{out}'
