from meeshkan.serve.utils.routing import HeaderRouting, PathRouting


def test_path_routing():
    routing = PathRouting()

    res = routing.route("/https://api.com/api/v1/entity/update", {})
    assert "api.com" == res.hostname
    assert "api.com" == res.host
    assert 443 == res.port
    assert "/api/v1/entity/update" == res.path
    assert "https" == res.scheme

    res = routing.route(
        "/http://api.com/api/v1/entity/update", {"Host": "localhost:8000"}
    )
    assert "api.com" == res.hostname
    assert "api.com" == res.host
    assert 80 == res.port
    assert "/api/v1/entity/update" == res.path
    assert "http" == res.scheme

    res = routing.route("/https://localhost:8443/api/v1/entity/update", {})
    assert "localhost" == res.hostname
    assert "localhost:8443" == res.host
    assert 8443 == res.port
    assert "/api/v1/entity/update" == res.path
    assert "https" == res.scheme


def test_header_routing():
    routing = HeaderRouting()

    res = routing.route(
        "/api/v1/entity/update", {"Host": "api.com"}, inbound_scheme="https"
    )
    assert "api.com" == res.hostname
    assert "api.com" == res.host
    assert 443 == res.port
    assert "/api/v1/entity/update" == res.path
    assert "https" == res.scheme

    res = routing.route("/api/v1/entity/update", {"Host": "api.com"})
    assert "api.com" == res.hostname
    assert "api.com" == res.host
    assert 80 == res.port
    assert "/api/v1/entity/update" == res.path
    assert "http" == res.scheme

    res = routing.route(
        "/api/v1/entity/update", {"Host": "localhost:8443"}, inbound_scheme="https"
    )
    assert "localhost" == res.hostname
    assert "localhost:8443" == res.host
    assert 8443 == res.port
    assert "/api/v1/entity/update" == res.path
    assert "https" == res.scheme
