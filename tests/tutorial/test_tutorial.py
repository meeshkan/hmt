from meeshkan.tutorial import CLI


def test_tutorial(event_loop):
    event_loop.run_until_complete(
        CLI(event_loop, use_real_input=False, throw_on_non_zero_exit=True).run()
    )
