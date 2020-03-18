from meeshkan.serve.mock.callbacks import callback


@callback("another.api.com", "post", "/echo", format="text", response="full")
def counter_callback_post(request_body, response):
    response["headers"]["X-Echo-Header"] = "value"
    response["body"] = request_body
    return response


@callback("another.api.com", "get", "/echo", response="full")
def counter_callback_get(query, response, storage):
    response["headers"]["X-Echo-Header"] = "value"
    response["bodyAsJson"] = {"message": query["message"]}
    return response
