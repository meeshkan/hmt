from tools.meeshkan_server.server.decorators import callback


@callback('api.imgur.com', 'get', '/hello/world')
def imgur_callback(request, response, storage):
    storage['called'] = storage.get('called', 0) + 1
    print('Hello from callback {} times'.format(storage['called']))
    return response