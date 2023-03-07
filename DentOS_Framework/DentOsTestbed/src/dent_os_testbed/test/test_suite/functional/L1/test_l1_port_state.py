import pytest, time
from dent_os_testbed.lib.ip.ip_link import IpLink

from dent_os_testbed.utils.test_utils.tgen_utils import (
    tgen_utils_get_dent_devices_with_tgen
)

from datetime import datetime

pytestmark = [
    pytest.mark.suite_functional_l1,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("cleanup_tgen")
]

async def port_state(testbed, counter, software_reboot = False):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 4)
    if not tgen_dev or not dent_devices:
        print("The testbed does not have enough dent with tgen connections")
        return
    dent_dev = dent_devices[0]
    device_host_name = dent_dev.host_name
    ports = tgen_dev.links_dict[device_host_name][1]
    timeout = 30

    for _ in range(counter):
        start_time = datetime.now()
        links_present = []
        for port in ports:
            rc, out = await dent_dev.run_cmd(f"ifconfig -a | grep -w '{port}' | wc -l")
            assert rc == 0, f"Failed to get a grep count of entities.\n"
            links_present.append(out.strip() == "1")
        if not all(links_present):
            time.sleep(timeout)
            for port in ports:
                rc, out = await dent_dev.run_cmd(f"ifconfig -a | grep -w '{port}' | wc -l")
                await сheck(rc, out, timeout)
        print(f"It took {datetime.now() - start_time} to grep count of entities.\n")

        out = await IpLink.set(
            input_data=[{device_host_name: [
                {"device": port, "operstate": "up"} for port in ports]}])
        assert out[0][device_host_name]["rc"] == 0, f"Verify that entities set to 'UP' state.\n{out}"

        start_time = datetime.now()
        for _ in range(20):
            out = await IpLink.show(input_data=[{device_host_name: [{"cmd_options": "-j"}]}],
                                    parse_output=True)
            assert out[0][device_host_name]["rc"] == 0, f"Failed to get links.\n"

            links = out[0][device_host_name]["parsed_output"]
            links_up = []
            for port in ports:
                for link in links:
                        if port in link["ifname"]:
                            links_up.append(link["operstate"] == "UP")
                            break
            if all(links_up):
                break
            time.sleep(timeout/6)
        else:
            assert all(links_up), f"One of the ports is not in the UP state.\n"
        print(f"It took {datetime.now() - start_time} to set entities to 'UP' state.\n")
        if software_reboot:
            await dent_dev.reboot()
            device_up = await dent_dev.is_connected()
            assert device_up == True, f"Verify that device: {dent_dev} is up!\n"

# verifying the availability of ports and their state Up/Down
async def сheck(rc, out, timeout):
    assert rc == 0, f"Failed to get a grep count of entities.\n"
    err_msg = f"FAIL: Not all ports exist and time is up, expected time <{timeout}.\n"
    assert out.strip() == "1", err_msg


async def test_l1_port_state_status(testbed):
    """
    Test Name: test_l1_port_state_status
    Test Suite: suite_functional_l1
    Test Overview: Verify port link and timings status.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Set entities swp1, swp2, swp3, swp4 UP state.
    2.  Verify the time it took for all ports to get up.
    """

    await port_state(testbed, 1)


async def test_l1_link_up_state_software_power_cycle(testbed):
    """
    Test Name: test_l1_link_up_state_software_power_cycle
    Test Suite: suite_functional_l1
    Test Overview: Verify port link and timings status due to software reboot.
    Test Author: Kostiantyn Stavruk
    Test Procedure:
    1.  Set entities swp1, swp2, swp3, swp4 UP state.
    2.  Verify the time it took for all ports to get up.
    3.  Software reboot.
    """

    await port_state(testbed, 2, software_reboot = True)
