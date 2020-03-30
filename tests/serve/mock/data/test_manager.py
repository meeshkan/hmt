from meeshkan.serve.mock.storage.manager import StorageManager
from tests.util import spec


def test_clear():
    manager = StorageManager()

    manager.add_mock("pokemon", spec())
    manager.add_mock("another", spec())

    manager["pokemon"]["x"] = "foo"
    manager["another"]["y"] = "bar"

    assert "foo" == manager["pokemon"]["x"]
    assert "bar" == manager["another"]["y"]

    manager.clear()

    assert manager["pokemon"].get("x") is None
    assert manager["another"].get("y") is None
