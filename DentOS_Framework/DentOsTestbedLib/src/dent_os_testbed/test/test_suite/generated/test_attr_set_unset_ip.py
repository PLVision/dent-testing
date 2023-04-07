# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# generated using file ./gen/model/test/network/ip/ip.yaml
#
# DONOT EDIT - generated by diligent bots

import pytest
import time
import re
from dent_os_testbed.utils.decorators import TestCaseSetup
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.test.lib.AttrSetAndUnset import AttrSetAndUnsetBase, AttrSetAndUnsetMeta
pytestmark = pytest.mark.suite_basic_trigger


class IpLinkAttrSetAndUnsetMeta(AttrSetAndUnsetMeta):
    """
    """
    def cls_name(obj=None):
        return 'ip_link'

    def set_fn(obj=None):
        return IpLink.set

    def show_fn(obj=None):
        return IpLink.show

    def dev_objects(obj=None):
        return obj.network.layer1.links

    def dev_object_filter(obj=None):
        return re.compile('swp*').match(obj.ifname) and obj.operstate == 'UP'

    def dev_object_set_params(obj=None):
        return {'device': obj.ifname, 'operstate':'down'}

    def dev_object_show_params(obj=None):
        return {'device': obj.ifname}

    def dev_object_reset_params(obj=None):
        return {'device': obj.ifname, 'operstate':'up'}


class IpLinkAttrSetAndUnset(AttrSetAndUnsetBase):
    """
    """
    meta = IpLinkAttrSetAndUnsetMeta


@pytest.fixture(params=[IpLinkAttrSetAndUnset,])
def attr_set_unset_ip_class(request):
    return request.param


@pytest.mark.asyncio
async def test_attr_set_unset_ip(testbed, attr_set_unset_ip_class):
    await attr_set_unset_ip_class().run_test(testbed)
