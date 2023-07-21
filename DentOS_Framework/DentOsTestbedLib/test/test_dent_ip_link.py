# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/dent/network/ip/link.yaml
#
# DONOT EDIT - generated by diligent bots

import asyncio

from dent_os_testbed.lib.ip.ip_link import IpLink

from .utils import TestDevice


def test_that_ip_link_add(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.add(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.add(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'name': 'bczpoyan',
                            'txqueuelen': 1509,
                            'address': 'bb:9d:cb:3a:15:75',
                            'broadcast': '5a:f3:8c:be:9b:91',
                            'mtu': 3593,
                            'gso_max_size': 6494,
                            'gso_max_segs': 3231,
                            'options': 'cyddpzft',
                        },
                        {
                            # command 2
                            'name': 'suejqumv',
                            'txqueuelen': 1008,
                            'address': '8d:91:34:ad:21:65',
                            'broadcast': '6e:06:4f:84:76:30',
                            'mtu': 5623,
                            'gso_max_size': 5355,
                            'gso_max_segs': 3757,
                            'options': 'rierncqn',
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.add(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'name': 'bczpoyan',
                            'txqueuelen': 1509,
                            'address': 'bb:9d:cb:3a:15:75',
                            'broadcast': '5a:f3:8c:be:9b:91',
                            'mtu': 3593,
                            'gso_max_size': 6494,
                            'gso_max_segs': 3231,
                            'options': 'cyddpzft',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'name': 'suejqumv',
                            'txqueuelen': 1008,
                            'address': '8d:91:34:ad:21:65',
                            'broadcast': '6e:06:4f:84:76:30',
                            'mtu': 5623,
                            'gso_max_size': 5355,
                            'gso_max_segs': 3757,
                            'options': 'rierncqn',
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_ip_link_delete(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.delete(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.delete(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'vvinuqwr',
                            'group': 'pqtytqgi',
                            'options': 'jvdvsgvo',
                        },
                        {
                            # command 2
                            'dev': 'eluwsgrx',
                            'group': 'axjolzed',
                            'options': 'mgpzsmri',
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.delete(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'vvinuqwr',
                            'group': 'pqtytqgi',
                            'options': 'jvdvsgvo',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'eluwsgrx',
                            'group': 'axjolzed',
                            'options': 'mgpzsmri',
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_ip_link_set(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.set(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.set(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'lphstpnf',
                            'group': 'chcypcvk',
                            'arp': True,
                            'dynamic': False,
                            'multicast': True,
                            'allmulticast': True,
                            'promiscuity': 778,
                            'txqueuelen': 2426,
                            'name': 'csurvuue',
                            'address': 'bf:37:2c:90:8e:1c',
                            'broadcast': 'e9:34:14:d8:bb:52',
                            'mtu': 9126,
                            'netns': 3907,
                            'alias': 'xlczxccc',
                            'vf': 9098,
                            'mac': 'eb:ff:b6:ac:15:5b',
                            'rate': 2345,
                            'max_tx_rate': 5109,
                            'min_tx_rate': 6613,
                            'spoofchk': 4088,
                            'state': 'wqplxfnv',
                            'master': 'jnjshzwm',
                            'nomaster': False,
                            'options': 'kxpscxkk',
                        },
                        {
                            # command 2
                            'dev': 'gxhdwzlx',
                            'group': 'urexidnq',
                            'arp': True,
                            'dynamic': False,
                            'multicast': False,
                            'allmulticast': False,
                            'promiscuity': 2506,
                            'txqueuelen': 935,
                            'name': 'hqajqzjr',
                            'address': '46:ca:6d:62:db:94',
                            'broadcast': '02:46:aa:14:22:08',
                            'mtu': 3886,
                            'netns': 3346,
                            'alias': 'uikqoxmk',
                            'vf': 4026,
                            'mac': '87:85:21:3e:02:4b',
                            'rate': 4968,
                            'max_tx_rate': 3997,
                            'min_tx_rate': 2579,
                            'spoofchk': 2717,
                            'state': 'ixysdpqq',
                            'master': 'nngfjkox',
                            'nomaster': False,
                            'options': 'npjjfduu',
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.set(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'lphstpnf',
                            'group': 'chcypcvk',
                            'arp': True,
                            'dynamic': False,
                            'multicast': True,
                            'allmulticast': True,
                            'promiscuity': 778,
                            'txqueuelen': 2426,
                            'name': 'csurvuue',
                            'address': 'bf:37:2c:90:8e:1c',
                            'broadcast': 'e9:34:14:d8:bb:52',
                            'mtu': 9126,
                            'netns': 3907,
                            'alias': 'xlczxccc',
                            'vf': 9098,
                            'mac': 'eb:ff:b6:ac:15:5b',
                            'rate': 2345,
                            'max_tx_rate': 5109,
                            'min_tx_rate': 6613,
                            'spoofchk': 4088,
                            'state': 'wqplxfnv',
                            'master': 'jnjshzwm',
                            'nomaster': False,
                            'options': 'kxpscxkk',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'gxhdwzlx',
                            'group': 'urexidnq',
                            'arp': True,
                            'dynamic': False,
                            'multicast': False,
                            'allmulticast': False,
                            'promiscuity': 2506,
                            'txqueuelen': 935,
                            'name': 'hqajqzjr',
                            'address': '46:ca:6d:62:db:94',
                            'broadcast': '02:46:aa:14:22:08',
                            'mtu': 3886,
                            'netns': 3346,
                            'alias': 'uikqoxmk',
                            'vf': 4026,
                            'mac': '87:85:21:3e:02:4b',
                            'rate': 4968,
                            'max_tx_rate': 3997,
                            'min_tx_rate': 2579,
                            'spoofchk': 2717,
                            'state': 'ixysdpqq',
                            'master': 'nngfjkox',
                            'nomaster': False,
                            'options': 'npjjfduu',
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_ip_link_show(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.show(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.show(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'vddezuwe',
                            'group': 'sumbzdlo',
                            'options': 'gtamvyob',
                        },
                        {
                            # command 2
                            'dev': 'roytjska',
                            'group': 'fxncoyvf',
                            'options': 'vdvxqurp',
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.show(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'vddezuwe',
                            'group': 'sumbzdlo',
                            'options': 'gtamvyob',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'roytjska',
                            'group': 'fxncoyvf',
                            'options': 'vdvxqurp',
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_ip_link_xstats(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.xstats(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.xstats(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'uhrfpysw',
                            'group': 'xsizssnp',
                            'options': 'xupyobhu',
                        },
                        {
                            # command 2
                            'dev': 'unaucrbb',
                            'group': 'ewnqrvvd',
                            'options': 'kuvdtmhw',
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.xstats(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'uhrfpysw',
                            'group': 'xsizssnp',
                            'options': 'xupyobhu',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'unaucrbb',
                            'group': 'ewnqrvvd',
                            'options': 'kuvdtmhw',
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0


def test_that_ip_link_afstats(capfd):

    dv1 = TestDevice(platform='dentos')
    dv2 = TestDevice(platform='dentos')
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.afstats(
            input_data=[
                {
                    # device 1
                    'test_dev': [{}],
                }
            ],
            device_obj={'test_dev': dv1},
        )
    )
    print(out)
    assert 'command' in out[0]['test_dev'].keys()
    assert 'result' in out[0]['test_dev'].keys()
    # check the rc
    assert out[0]['test_dev']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.afstats(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            # command 1
                            'dev': 'gdadpsfl',
                            'group': 'gvkmnxqd',
                            'options': 'ijhlpnbt',
                        },
                        {
                            # command 2
                            'dev': 'rsaszsyr',
                            'group': 'bezevcls',
                            'options': 'skabowpn',
                        },
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(
        IpLink.afstats(
            input_data=[
                {
                    # device 1
                    'test_dev1': [
                        {
                            'dev': 'gdadpsfl',
                            'group': 'gvkmnxqd',
                            'options': 'ijhlpnbt',
                        }
                    ],
                    # device 2
                    'test_dev2': [
                        {
                            'dev': 'rsaszsyr',
                            'group': 'bezevcls',
                            'options': 'skabowpn',
                        }
                    ],
                }
            ],
            device_obj={'test_dev1': dv1, 'test_dev2': dv2},
        )
    )
    print(out)
    # check if the command was formed
    assert 'command' in out[0]['test_dev1'].keys()
    assert 'command' in out[1]['test_dev2'].keys()
    # check if the result was formed
    assert 'result' in out[0]['test_dev1'].keys()
    assert 'result' in out[1]['test_dev2'].keys()
    # check the rc
    assert out[0]['test_dev1']['rc'] == 0
    assert out[1]['test_dev2']['rc'] == 0
