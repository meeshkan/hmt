import pytest

from hmt.tutorial import CLI


@pytest.mark.asyncio()
async def test_tut(event_loop):
    await CLI(event_loop, use_real_input=False, throw_on_non_zero_exit=True).run()
