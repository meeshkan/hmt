import asyncio

from meeshkan.tutorial import CLI


def test_tutorial():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(CLI(loop, use_real_input=False, throw_on_non_zero_exit=True).run())
