from meeshkan.server.server.callbacks import callback


@callback('api.com', 'post', '/counter')
def counter_callback(request_body, response_body, storage):
    if 'set' in request_body:
        storage['called'] = request_body['set']
    else:
        storage['called'] = storage.get('called', 0) + 1
    response_body['count'] = storage['called']
    return response_body

@callback('api.com', 'get', '/text_counter', format='text')
def counter_callback(query, response_body, storage):
    if 'set' in query:
        storage['called'] = query['set']
    else:
        storage['called'] = storage.get('called', 0) + 1
    return "{} {} times".format(response_body, storage['called'])