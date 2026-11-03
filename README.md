# tiny-json

> Zero-dependency JSON pipeline for Python. Query, transform, merge, and validate — all in one file.

## Why?

Agents deal with messy JSON from LLMs and APIs all day. You need to extract fields, rename them for your internal tools, and merge them into state. `jq` is a separate binary. `jsonpath-ng` is a dependency.

**tiny-json** gives you a fluent API for JSON manipulation in ~80 lines of pure Python.

## 📦 Install

```bash
pip install tiny-json
```

Or just copy `tiny_json.py` into your project - it has **zero dependencies**.

## Usage

```python
from tiny_json import JSONPipeline

data = {
    "items": [
        {"id": "A1", "info": {"price": 10, "label": "Widget"}},
        {"id": "B2", "info": {"price": 20, "label": "Gadget"}}
    ]
}

p = JSONPipeline(data)

# Query and Transform
catalog = p.query("items").transform({
    "sku": "id",
    "cost": "info.price",
    "name": "info.label"
})

print(catalog.data)
# [{'sku': 'A1', 'cost': 10, 'name': 'Widget'}, ...]

# Deep Merge
state = {"user": {"id": 1, "settings": {"theme": "dark"}}}
update = {"user": {"settings": {"notifications": True}}}

new_state = JSONPipeline(state).merge(update).data
# {'user': {'id': 1, 'settings': {'theme': 'dark', 'notifications': True}}}
```

## Features

- **Query**: Dot-notation access for nested dicts and lists.
- **Transform**: Map source paths to new keys or run callables.
- **Merge**: Deep recursive merge for state updates.
- **Validate**: Lightweight type checking.
- **Zero Deps**: Stdlib only.

## 🧪 Testing

```bash
python -m pytest tests/
```

## 📄 License

MIT - see [LICENSE](LICENSE).

---

Built by [Hussain Al-Saibai](https://github.com/hussain-alsaibai) as part of the [`dev-masterkit`](https://github.com/hussain-alsaibai/dev-masterkit) ecosystem.
