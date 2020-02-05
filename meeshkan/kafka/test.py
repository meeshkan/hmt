import asyncio
import faust


class Greeting(faust.Record):
    from_name: str
    to_name: str


app = faust.App('hello-app', broker='kafka://localhost')
topic = app.topic('hello-topic', value_type=Greeting)


@app.agent(topic)
async def hello(greetings):
    async for greeting in greetings:
        print(f'Hello from {greeting.from_name} to {greeting.to_name}')


@app.timer(interval=1.0)
async def example_sender(app):
    await hello.send(
        value=Greeting(from_name='Faust', to_name='you'),
    )


async def start_worker(worker: faust.Worker) -> None:
    await worker.start()


def start_in_loop(app):
    loop = asyncio.get_event_loop()
    task = loop.create_task(app.start())
    loop.run_until_complete(task)


def manage_loop():
    loop = asyncio.get_event_loop()
    worker = faust.Worker(app, loop=loop, loglevel='info')
    try:
        loop.run_until_complete(start_worker(worker))
    finally:
        # worker.stop_and_shutdown_loop()
        worker.stop_and_shutdown()


if __name__ == '__main__':
    # start_in_loop(app)
    manage_loop()
