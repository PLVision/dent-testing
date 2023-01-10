import pytest
from dent_os_testbed.lib.ip.ip_link import IpLink
from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen


@pytest.fixture(scope="session")
async def configure_vlan_setup(testbed):
    """
    Fixture performs following steps:
        1.Create bridge entity and set state to "up" state.
        2.Create links and set state to `up`.
        3.Set bridge as master to links.
    """
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    device = dent_devices[0]
    ports = tgen_dev.links_dict[device][1]
    device.applog.info("Create bridge entity")
    out = await IpLink.add(input_data=[{device: [{"device": "br0", "type": "bridge", "vlan_filtering": 1}]}])
    assert out[0][device]["rc"] == 0, f"Verify bridge entity created.\n {out}"

    device.applog.info("Set bridge entity to 'up' state")
    await IpLink.set(input_data=[{device: [{"device": "br0", "operstate": "up"}]}])
    assert out[0][device]["rc"] == 0, f"Verify bridge entity set to 'up' state.\n {out}"

    device.applog.info("Create links and set state to `up`")
    await IpLink.add(input_data=[{device: [{"device": f"{port}"} for port in ports]}])
    out = await IpLink.set(input_data=[{device: [{"device": f"{port}", "operstate": "up"} for port in ports]}])
    assert out[0][device]["rc"] == 0, f"Verify links are created and put to 'up' state.\n {out}"

    device.applog.info("Set bridge as master to links.")
    await IpLink.set(input_data=[{device: [{"device": f"{port}", "master": "br0"} for port in ports]}])
    assert out[0][device]["rc"] == 0, f"Verify links enslaved to bridge.\n {out}"
