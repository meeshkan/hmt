HttpExchangeStream = AsyncIterable[HttpExchange]
BuildResultStream = AsyncIterable[BuildResult]

Source = Callable[[AbstractEventLoop], HttpExchangeStream]
Sink = Callable[[BuildResultStream], Awaitable[None]]
