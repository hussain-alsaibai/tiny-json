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
            elif isinstance(curr, list) and part.isdigit():
                curr = curr[int(part)]
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
        def _merge(a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                res = a.copy()
                for k, v in b.items():
                    if k in res:
                        res[k] = _merge(res[k], v)
                    else:
                        res[k] = v
                return res
            return b if overwrite else a
        
        return JSONPipeline(_merge(self.data, other))

    def validate(self, schema: Dict[str, type]) -> bool:
        """Basic type validation for flat or nested dicts."""
        if not isinstance(self.data, dict):
            return False
        for k, t in schema.items():
            val = self.query(k).data
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
