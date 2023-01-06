import pytest

pytestmark = pytest.mark.suite_my

@pytest.fixture
def add_cleanup():
    stack = []
    def append_to_stack(func, *args, **kwargs):
        if callable(func):
            stack.append((func, (*args,), {**kwargs}))
    yield append_to_stack

    for func, args, kwargs in stack:
        func(*args, **kwargs)

@pytest.mark.asyncio
async def test_cleanup_fixture(testbed, add_cleanup):
    add_cleanup(print, "asd", 123)
