from meeshkan.serve.mock.data.storage import storage_manager


def test_clear():
    storage = storage_manager.default
    storage.default["x"] = "y"

    storage.add_entity("default")

    assert "y" == storage.default["x"]

    storage.clear()

    assert "x" not in storage.default
