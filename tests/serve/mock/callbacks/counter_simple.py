from meeshkan.serve.mock.callbacks import callback


@callback("api.imgur.com", "post", "/counter")
def counter_callback(request_body, response_body, storage):
    if "set" in request_body:
        storage["called"] = request_body["set"]
    else:
        storage["called"] = storage.get("called", 0) + 1
    response_body["count"] = storage["called"]
    return response_body
