import pytest_asyncio
import pytest

from dent_os_testbed.utils.test_utils.tgen_utils import tgen_utils_get_dent_devices_with_tgen

from dent_os_testbed.test.test_suite.functional.ifupdown2.ifupdown2_utils import (
    IFUPDOWN_CONF, IFUPDOWN_BACKUP,
    INTERFACES_FILE,
)


@pytest_asyncio.fixture()
async def prepare_env(testbed):
    tgen_dev, dent_devices = await tgen_utils_get_dent_devices_with_tgen(testbed, [], 0)
    if not tgen_dev or not dent_devices:
        pytest.skip('The testbed does not have enough dent with tgen connections')
    dent_dev = dent_devices[0]

    # Get Default values
    settings = ['template_lookuppath', 'addon_syntax_check', 'default_interfaces_configfile']
    rc, out = await dent_dev.run_cmd(f'cat {IFUPDOWN_CONF}')
    defaults = {setting: line.strip().split('=')[-1] for setting in settings
                for line in out.splitlines() if setting in line}

    # Make backup's
    rc, out = await dent_dev.run_cmd(f'cp {IFUPDOWN_CONF} {IFUPDOWN_BACKUP}', sudo=True)
    assert not rc, f'Failed to copy.\n{out}'
    rc, out = await dent_dev.run_cmd(f'cp {defaults["default_interfaces_configfile"]} {INTERFACES_FILE}', sudo=True)
    assert not rc, f'Failed to copy.\n{out}'

    async def apply_config(dent_dev, fields, config_file=IFUPDOWN_CONF):
        # Prep env and change it
        opts = [f's~^{k}=.*~{k}={v}~' for k, v in fields.items()]
        rc, out = await dent_dev.run_cmd(f'sed -i -E "{"; ".join(opts)}" {config_file}')
        return rc

    yield apply_config

    try:
        rc = await apply_config(dent_dev, defaults)
        assert not rc, f'Error during apply of ifupdown2 config {rc}'
    except AssertionError:
        rc, out = await dent_dev.run_cmd(f'cp {IFUPDOWN_BACKUP} {IFUPDOWN_CONF}')

    rc, out = await dent_dev.run_cmd('ifreload -a -v')
    assert not rc, 'Failed to reload ifupdown2 config'
