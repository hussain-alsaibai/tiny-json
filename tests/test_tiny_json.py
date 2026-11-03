import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tiny_json import JSONPipeline


class TestQuery(unittest.TestCase):
    def test_query_nested_dict(self):
        p = JSONPipeline({"user": {"profile": {"name": "Alice"}}})
        self.assertEqual(p.query("user.profile.name").data, "Alice")

    def test_query_list_index(self):
        p = JSONPipeline({"items": [{"id": "A"}, {"id": "B"}]})
        self.assertEqual(p.query("items.1.id").data, "B")

    def test_query_missing_path_returns_none(self):
        p = JSONPipeline({"a": 1})
        self.assertIsNone(p.query("nope.deeper").data)

    def test_query_is_chainable(self):
        p = JSONPipeline({"a": {"b": {"c": 1}}})
        self.assertEqual(p.query("a").query("b").query("c").data, 1)

    def test_from_str(self):
        p = JSONPipeline.from_str('{"x": 5}')
        self.assertEqual(p.query("x").data, 5)


class TestTransform(unittest.TestCase):
    def test_transform_renames_keys(self):
        p = JSONPipeline({"id": "A1", "info": {"price": 10}})
        out = p.transform({"sku": "id", "cost": "info.price"})
        self.assertEqual(out.data, {"sku": "A1", "cost": 10})

    def test_transform_applies_callable(self):
        p = JSONPipeline({"v": 2})
        out = p.transform({"double": lambda item: item["v"] * 2})
        self.assertEqual(out.data, {"double": 4})

    def test_transform_applies_to_each_list_item(self):
        p = JSONPipeline([{"id": 1}, {"id": 2}])
        out = p.transform({"n": "id"})
        self.assertEqual(out.data, [{"n": 1}, {"n": 2}])

    def test_transform_on_non_container_is_noop(self):
        p = JSONPipeline("plain")
        self.assertIs(p.transform({"x": "y"}), p)

    def test_transform_does_not_mutate_source(self):
        src = {"id": 1}
        p = JSONPipeline(src)
        p.transform({"n": "id"})
        self.assertEqual(src, {"id": 1})


class TestMerge(unittest.TestCase):
    def test_merge_is_deep(self):
        a = {"user": {"id": 1, "settings": {"theme": "dark"}}}
        b = {"user": {"settings": {"notifications": True}}}
        out = JSONPipeline(a).merge(b)
        self.assertEqual(
            out.data,
            {"user": {"id": 1, "settings": {"theme": "dark", "notifications": True}}},
        )

    def test_merge_overwrite_false_keeps_original(self):
        a = {"x": 1}
        b = {"x": 2}
        out = JSONPipeline(a).merge(b, overwrite=False)
        self.assertEqual(out.data, {"x": 1})

    def test_merge_overwrite_true_takes_new(self):
        out = JSONPipeline({"x": 1}).merge({"x": 2})
        self.assertEqual(out.data, {"x": 2})

    def test_merge_does_not_mutate_source(self):
        a = {"user": {"id": 1}}
        JSONPipeline(a).merge({"user": {"id": 2}})
        self.assertEqual(a, {"user": {"id": 1}})

    def test_merge_adds_new_keys(self):
        out = JSONPipeline({"a": 1}).merge({"b": 2})
        self.assertEqual(out.data, {"a": 1, "b": 2})


class TestValidate(unittest.TestCase):
    def test_validate_accepts_matching_types(self):
        p = JSONPipeline({"a": 1, "b": "s"})
        self.assertTrue(p.validate({"a": int, "b": str}))

    def test_validate_rejects_wrong_type(self):
        p = JSONPipeline({"a": "not an int"})
        self.assertFalse(p.validate({"a": int}))

    def test_validate_ignores_missing_keys(self):
        p = JSONPipeline({"a": 1})
        self.assertTrue(p.validate({"a": int, "missing": str}))

    def test_validate_on_non_dict_is_false(self):
        self.assertFalse(JSONPipeline([1, 2]).validate({"a": int}))

    def test_validate_accepts_none_value(self):
        p = JSONPipeline({"a": None})
        self.assertTrue(p.validate({"a": int}))


class TestToJson(unittest.TestCase):
    def test_to_json_roundtrips(self):
        import json

        data = {"a": [1, 2], "b": {"c": True}}
        out = JSONPipeline(data).to_json()
        self.assertEqual(json.loads(out), data)

    def test_to_json_indent(self):
        out = JSONPipeline({"a": 1}).to_json(indent=4)
        self.assertIn("\n    ", out)


if __name__ == "__main__":
    unittest.main()
