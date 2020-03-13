from typing import Any


class MeeshkanFakerBase:
    def fake_it(self, schema: Any, top_schema: Any, depth: int) -> Any:
        raise NotImplementedError
