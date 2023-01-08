import json
import pytest

from dent_os_testbed.lib.bridge.bridge_vlan import BridgeVlan
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

pytestmark = pytest.mark.suite_functional_vlan


@pytest.mark.asyncio
async def test_max_vlans(testbed):
    """
    Test Name: Maximum vlans for the interface
    Test Suite: suite_functional_vlan
    Test Overview: Test maximum number of vlans that can be set on interface
    Test Procedure:
    1. Initiate test params
    2. Create bridge entity and set state to "up" state.
    3. Enslave interface to the created bridge entity.
    4. Insert interface to all VLANs possible(4094)
    5. Verify interface is in all possible(4094) VLANs
    """

    max_vlans = 4094
    #  1.Initiate test params
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 1)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    device = dent_devices[0].host_name
    ports = tgen_dev.links_dict[device][1]
    test_port = ports[0]

    #  2.Create bridge entity and set state to "up" state
    await IpLink.add(input_data=[{device: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}])
    out = await IpLink.set(input_data=[{device: [{"device": "br0", "operstate": "up"}]}])
    assert out[0][device]["rc"] == 0, f" Verify bridge entity created and bridge entity set to 'up' state.\n {out}"

    await IpLink.add(input_data=[{device: [{"device": f"{test_port}", "type": "veth"}]}])
    out = await IpLink.set(input_data=[{device: [{"device": f"{test_port}", "operstate": "up"}]}])

    # 3. Enslave interface to the created bridge entity
    await IpLink.set(input_data=[{device: [{"device": f"{test_port}", "master": "br0"}]}])
    assert out[0][device]["rc"] == 0, f" Verify links enslaved to bridge.\n {out}"

    # 4. Insert interface to all VLANs possible
    cmd = f"time for i in {{1..{max_vlans}}}; do bridge vlan add vid $i dev {test_port}; done"
    await dent_devices[0].run_cmd(cmd)

    # 5. Verify interface is in all possible(4094) VLANs
    out = await BridgeVlan.show(input_data=[{device: [{"device": test_port, "cmd_options": "-j"}]}])
    vlans = json.loads(out[0][device]["result"])
    assert len(vlans[0]["vlans"]) == max_vlans, f"Not all VLANS has been added to {test_port} on {device} device \n"


@pytest.mark.asyncio
async def test_add_interface_to_vlan_wo_bridge(testbed):
    """
    Test Name: Add  interface to vlan without enslaving to bridge entity
    Test Suite: suite_functional_vlan
    Test Overview: Test that interface can not be added to VLAN without bridge entity
    Test Procedure:
    1. Initiate test params
    2. Insert interface to any VLAN
       Verify adding interface to VLAN fails
    3. Create bridge entity.
    4. Insert interface to any VLAN
       Verify adding interface to VLAN fails
    """

    # 1.Initiate test params
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 1)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgn connections")
        return
    device = dent_devices[0].host_name
    ports = tgen_dev.links_dict[device][1]
    test_port = ports[0]
    out = await IpLink.add(input_data=[{device: [{"device": f"{test_port}", "type": "veth"}]}])
    assert out[0][device]["rc"] == 0

    # 2. Insert interface to any VLAN. Verify adding interface to VLAN fails
    out = await BridgeVlan.add(input_data=[{device: [{"device": test_port, "vid": 2}]}])
    assert "RTNETLINK answers: Operation not supported" in out[0][device]["result"]

    # 3. Create bridge entity.
    await IpLink.add(input_data=[{device: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}])
    out = await IpLink.set(input_data=[{device: [{"device": "br0", "operstate": "up"}]}])
    assert out[0][device]["rc"] == 0

    # Insert interface to any VLAN. Verify adding interface to VLAN fails
    out = await BridgeVlan.add(input_data=[{device: [{"device": test_port, "vid": 2}]}])
    assert "RTNETLINK answers: Operation not supported" in out[0][device]["result"]
