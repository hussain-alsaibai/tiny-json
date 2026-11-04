"""Regression tests for defects found 2026-11-03."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tiny_json import JSONPipeline


def test_query_on_empty_list_does_not_raise():
    """An absent index is an absent value, not an exception.

    ``query`` returns ``JSONPipeline(None)`` for every other miss (missing key,
    non-numeric list segment). Only an out-of-range index raised
    ``IndexError``, so a chained query over an empty API array -- the common
    case -- crashed instead of yielding None.
    """
    assert JSONPipeline({"items": []}).query("items.0.name").data is None
    assert JSONPipeline({"items": [{"id": 1}]}).query("items.5.id").data is None


def test_merge_overwrite_false_does_not_merge_nested_dicts():
    """``overwrite=False`` means "keep what a has", at every depth.

    The flag was only consulted at non-dict leaves. A key that was a dict on
    both sides was deep-merged anyway, so nested values from ``b`` appeared in
    the result even though the caller asked to keep ``a``'s.
    """
    out = JSONPipeline({"cfg": {"x": 1}}).merge({"cfg": {"y": 2}}, overwrite=False)
    assert out.data == {"cfg": {"x": 1}}


def test_merge_overwrite_false_still_adds_new_keys():
    """The flag must not turn merge into a no-op for genuinely new keys."""
    out = JSONPipeline({"cfg": {"x": 1}}).merge({"other": 2}, overwrite=False)
    assert out.data == {"cfg": {"x": 1}, "other": 2}


def test_merge_result_does_not_alias_the_source():
    """Mutating a merge result must not write through to the input.

    ``_merge`` copied only the top level of dicts that existed on one side,
    so nested dicts were shared. A caller updating merged state silently
    corrupted the object it merged from.
    """
    source = {"n": {"v": 1}}
    merged = JSONPipeline(source).merge({"z": 9}).data
    merged["n"]["v"] = 99
    assert source == {"n": {"v": 1}}, "merge result leaked a reference to the source"


def test_merge_result_does_not_alias_the_other_argument():
    other = {"n": {"v": 2}}
    merged = JSONPipeline({"z": 1}).merge(other).data
    merged["n"]["v"] = 99
    assert other == {"n": {"v": 2}}


def test_validate_can_require_every_key():
    """The default stays lenient; ``require_all=True`` is the opt-in.

    ``validate`` could not express "this key is required" at all: a missing
    key, and a key that was present as ``None``, both passed. That is a
    sensible default for loose JSON, but there was no way to ask for the
    strict version, so callers guarding an invariant had no safe option.
    """
    data = JSONPipeline({"a": 1})
    assert data.validate({"a": int, "b": str}) is True
    assert data.validate({"a": int, "b": str}, require_all=True) is False
    assert JSONPipeline({"a": None}).validate({"a": int}, require_all=True) is False
    assert JSONPipeline({"a": 1, "b": "x"}).validate(
        {"a": int, "b": str}, require_all=True
    ) is True
    assert JSONPipeline({"a": 1, "b": 2}).validate(
        {"a": int, "b": str}, require_all=True
    ) is False
