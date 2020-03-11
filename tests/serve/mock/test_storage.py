from meeshkan.serve.mock.storage import storage_manager


def test_clear():
    storage_manager.default["x"] = "y"
    assert storage_manager.get("default") is None

    storage_manager.add_storage("default")
    storage_manager.get("default")["x"] = "z"

    assert "y" == storage_manager.default["x"]
    assert "z" == storage_manager.get("default")["x"]

    storage_manager.clear()

    assert "x" not in storage_manager.default
    assert "z" not in storage_manager.get("default")
