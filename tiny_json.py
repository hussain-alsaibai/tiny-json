import json
from typing import Any, Callable, Dict, Union

class JSONPipeline:
    """Zero-dependency JSON pipeline: validate, transform, merge, query."""
    
    def __init__(self, data: Any = None):
        self.data = data

    @classmethod
    def from_str(cls, s: str) -> "JSONPipeline":
        return cls(json.loads(s))

    def query(self, path: str) -> "JSONPipeline":
        """Simple dot-notation query: 'user.profile.name'"""
        parts = path.split(".")
        curr = self.data
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            elif isinstance(curr, list) and part.lstrip("-").isdigit():
                # An index past the end is an absent value, exactly like a
                # missing key. Raising IndexError broke every chained query
                # over an empty API array.
                try:
                    curr = curr[int(part)]
                except IndexError:
                    return JSONPipeline(None)
            else:
                return JSONPipeline(None)
        return JSONPipeline(curr)

    def transform(self, mapping: Dict[str, Union[str, Callable]]) -> "JSONPipeline":
        """Transform data using a mapping of target_key -> source_path or callable."""
        if not isinstance(self.data, (dict, list)):
            return self
        
        def _apply(item):
            out = {}
            for k, v in mapping.items():
                if callable(v):
                    out[k] = v(item)
                else:
                    out[k] = JSONPipeline(item).query(v).data
            return out

        if isinstance(self.data, list):
            return JSONPipeline([_apply(i) for i in self.data])
        return JSONPipeline(_apply(self.data))

    def merge(self, other: Any, overwrite: bool = True) -> "JSONPipeline":
        """Deep merge two objects."""
        def _copy(value):
            # Copy on the way in so the result shares no nested object with
            # either argument; _merge used to alias them.
            if isinstance(value, dict):
                return {k: _copy(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_copy(v) for v in value]
            return value

        def _merge(a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                res = _copy(a)
                for k, v in b.items():
                    if k in res:
                        if isinstance(res[k], dict) and isinstance(v, dict):
                            if not overwrite:
                                # "Keep what a has" applies at every depth,
                                # not only at leaves.
                                continue
                            res[k] = _merge(res[k], v)
                        else:
                            res[k] = _copy(v) if overwrite else res[k]
                    else:
                        res[k] = _copy(v)
                return res
            return _copy(b) if overwrite else _copy(a)
        
        return JSONPipeline(_merge(self.data, other))

    def validate(self, schema: Dict[str, type], require_all: bool = False) -> bool:
        """Basic type validation for flat or nested dicts.

        By default a key that is absent -- or present as ``None`` -- counts as
        valid, which is what "lightweight type checking" has always meant here
        and what the existing tests pin. Pass ``require_all=True`` to also
        demand that every key in the schema is present and non-``None``:

            >>> JSONPipeline({"a": 1}).validate({"a": int, "b": str})
            True
            >>> JSONPipeline({"a": 1}).validate({"a": int, "b": str}, require_all=True)
            False
        """
        if not isinstance(self.data, dict):
            return False
        for k, t in schema.items():
            missing = k not in self.data
            val = self.query(k).data
            if require_all and (missing or val is None):
                return False
            if val is not None and not isinstance(val, t):
                return False
        return True

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.data, indent=indent)

# Example usage
if __name__ == "__main__":
    raw = '{"users": [{"id": 1, "meta": {"name": "Alice"}}, {"id": 2, "meta": {"name": "Bob"}}]}'
    p = JSONPipeline.from_str(raw)
    names = p.query("users").transform({"user_name": "meta.name", "uid": "id"})
    print(names.to_json())
