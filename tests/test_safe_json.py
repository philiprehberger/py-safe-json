from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path, PurePosixPath
from uuid import UUID

import pytest

from philiprehberger_safe_json import (
    CircularReferenceError,
    SafeJsonEncoder,
    clear_encoders,
    dumps,
    loads,
    register_encoder,
    safe_loads,
)


def test_datetime_encodes_to_iso_string() -> None:
    dt = datetime(2026, 3, 13, 14, 30, 0)
    result = json.loads(dumps({"ts": dt}))
    assert result["ts"] == "2026-03-13T14:30:00"


def test_date_encodes_to_iso_string() -> None:
    d = date(2026, 3, 13)
    result = json.loads(dumps({"day": d}))
    assert result["day"] == "2026-03-13"


def test_decimal_encodes_to_float_by_default() -> None:
    result = json.loads(dumps({"price": Decimal("19.99")}))
    assert result["price"] == 19.99
    assert isinstance(result["price"], float)


def test_decimal_encodes_to_string_with_option() -> None:
    result = json.loads(dumps({"price": Decimal("19.99")}, decimal_as_string=True))
    assert result["price"] == "19.99"
    assert isinstance(result["price"], str)


def test_uuid_encodes_to_string() -> None:
    uid = UUID("12345678-1234-5678-1234-567812345678")
    result = json.loads(dumps({"id": uid}))
    assert result["id"] == "12345678-1234-5678-1234-567812345678"


def test_dataclass_encodes_to_dict() -> None:
    @dataclass
    class Point:
        x: int
        y: int

    result = json.loads(dumps({"point": Point(x=1, y=2)}))
    assert result["point"] == {"x": 1, "y": 2}


def test_set_encodes_to_sorted_list() -> None:
    result = json.loads(dumps({"tags": {"c", "a", "b"}}))
    assert result["tags"] == ["a", "b", "c"]


def test_frozenset_encodes_to_sorted_list() -> None:
    result = json.loads(dumps({"tags": frozenset({"z", "m", "a"})}))
    assert result["tags"] == ["a", "m", "z"]


def test_bytes_encodes_to_base64() -> None:
    result = json.loads(dumps({"data": b"hello"}))
    assert result["data"] == "aGVsbG8="


def test_enum_encodes_to_value() -> None:
    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    result = json.loads(dumps({"color": Color.RED}))
    assert result["color"] == "red"


def test_int_enum_encodes_to_value() -> None:
    class Priority(Enum):
        LOW = 1
        HIGH = 3

    result = json.loads(dumps({"priority": Priority.HIGH}))
    assert result["priority"] == 3


def test_path_encodes_to_string() -> None:
    result = json.loads(dumps({"file": PurePosixPath("/home/user/data.txt")}))
    assert result["file"] == "/home/user/data.txt"


def test_nested_structure_with_mixed_types() -> None:
    @dataclass
    class Item:
        name: str
        price: Decimal

    data = {
        "created": datetime(2026, 1, 1, 0, 0, 0),
        "items": [Item(name="Widget", price=Decimal("5.50"))],
        "tags": {"sale", "new"},
        "id": UUID("abcdef01-2345-6789-abcd-ef0123456789"),
    }
    result = json.loads(dumps(data))
    assert result["created"] == "2026-01-01T00:00:00"
    assert result["items"] == [{"name": "Widget", "price": 5.5}]
    assert result["tags"] == ["new", "sale"]
    assert result["id"] == "abcdef01-2345-6789-abcd-ef0123456789"


def test_regular_types_pass_through() -> None:
    data = {"name": "test", "count": 42, "items": [1, 2, 3], "nested": {"a": True}}
    result = json.loads(dumps(data))
    assert result == data


def test_loads_works_as_pass_through() -> None:
    raw = '{"key": "value", "num": 123}'
    result = loads(raw)
    assert result == {"key": "value", "num": 123}


def test_loads_with_bytes() -> None:
    raw = b'{"key": "value"}'
    result = loads(raw)
    assert result == {"key": "value"}


def test_round_trip_simple_types() -> None:
    original = {"name": "test", "count": 42, "flag": True, "empty": None}
    result = loads(dumps(original))
    assert result == original


def test_unknown_custom_object_raises_type_error() -> None:
    class Custom:
        pass

    with pytest.raises(TypeError):
        dumps({"obj": Custom()})


def test_encoder_used_directly_with_json_dumps() -> None:
    dt = datetime(2026, 6, 15, 8, 0, 0)
    result = json.loads(json.dumps({"ts": dt}, cls=SafeJsonEncoder))
    assert result["ts"] == "2026-06-15T08:00:00"


def test_empty_dict() -> None:
    assert dumps({}) == "{}"


def test_empty_list() -> None:
    assert dumps([]) == "[]"


def test_none_values() -> None:
    result = json.loads(dumps({"a": None, "b": None}))
    assert result == {"a": None, "b": None}


# --- Custom type encoder registration tests ---


class TestRegisterEncoder:
    def setup_method(self) -> None:
        clear_encoders()

    def teardown_method(self) -> None:
        clear_encoders()

    def test_register_custom_type(self) -> None:
        class Money:
            def __init__(self, amount: int, currency: str) -> None:
                self.amount = amount
                self.currency = currency

        register_encoder(Money, lambda m: {"amount": m.amount, "currency": m.currency})
        result = json.loads(dumps({"payment": Money(1000, "USD")}))
        assert result["payment"] == {"amount": 1000, "currency": "USD"}

    def test_register_encoder_with_string_return(self) -> None:
        class Color:
            def __init__(self, r: int, g: int, b: int) -> None:
                self.r = r
                self.g = g
                self.b = b

        register_encoder(Color, lambda c: f"#{c.r:02x}{c.g:02x}{c.b:02x}")
        result = json.loads(dumps({"color": Color(255, 128, 0)}))
        assert result["color"] == "#ff8000"

    def test_registered_encoder_works_with_subclass(self) -> None:
        class Animal:
            def __init__(self, name: str) -> None:
                self.name = name

        class Dog(Animal):
            pass

        register_encoder(Animal, lambda a: a.name)
        result = json.loads(dumps({"pet": Dog("Rex")}))
        assert result["pet"] == "Rex"

    def test_clear_encoders_removes_all(self) -> None:
        class Foo:
            pass

        register_encoder(Foo, lambda f: "foo")
        clear_encoders()
        with pytest.raises(TypeError):
            dumps({"obj": Foo()})

    def test_builtin_types_take_priority(self) -> None:
        """Custom encoders should not override built-in type handling."""
        register_encoder(datetime, lambda d: "custom")
        result = json.loads(dumps({"ts": datetime(2026, 1, 1)}))
        # Built-in handler runs first
        assert result["ts"] == "2026-01-01T00:00:00"

    def test_multiple_custom_types(self) -> None:
        class TypeA:
            pass

        class TypeB:
            pass

        register_encoder(TypeA, lambda _: "a")
        register_encoder(TypeB, lambda _: "b")
        result = json.loads(dumps({"a": TypeA(), "b": TypeB()}))
        assert result == {"a": "a", "b": "b"}


# --- Circular reference detection tests ---


class TestCircularReferenceDetection:
    def test_dict_circular_reference(self) -> None:
        a: dict[str, Any] = {"key": "value"}
        a["self"] = a
        with pytest.raises(CircularReferenceError):
            dumps(a, detect_cycles=True)

    def test_list_circular_reference(self) -> None:
        a: list[Any] = [1, 2]
        a.append(a)
        with pytest.raises(CircularReferenceError):
            dumps({"items": a}, detect_cycles=True)

    def test_nested_circular_reference(self) -> None:
        a: dict[str, Any] = {}
        b: dict[str, Any] = {"parent": a}
        a["child"] = b
        with pytest.raises(CircularReferenceError):
            dumps(a, detect_cycles=True)

    def test_no_circular_reference_passes(self) -> None:
        data = {"a": [1, 2, {"b": "c"}], "d": {"e": [3, 4]}}
        result = json.loads(dumps(data, detect_cycles=True))
        assert result == data

    def test_detect_cycles_false_does_not_check(self) -> None:
        """With detect_cycles=False (default), no check is performed."""
        data = {"a": 1, "b": [2, 3]}
        result = json.loads(dumps(data, detect_cycles=False))
        assert result == data

    def test_shared_references_not_flagged(self) -> None:
        """Same object referenced multiple times (not circular) should work."""
        shared = [1, 2, 3]
        data = {"a": shared, "b": shared}
        result = json.loads(dumps(data, detect_cycles=True))
        assert result == {"a": [1, 2, 3], "b": [1, 2, 3]}

    def test_dataclass_circular_reference(self) -> None:
        @dataclass
        class Node:
            value: int
            children: list[Any]

        node = Node(value=1, children=[])
        node.children.append(node)
        with pytest.raises(CircularReferenceError):
            dumps(node, detect_cycles=True)

    def test_circular_reference_error_message(self) -> None:
        a: dict[str, Any] = {}
        a["self"] = a
        with pytest.raises(CircularReferenceError, match="Circular reference detected"):
            dumps(a, detect_cycles=True)


# --- safe_loads tests ---


class TestSafeLoads:
    def test_parse_datetime_string(self) -> None:
        raw = '{"created": "2026-03-13T14:30:00"}'
        result = safe_loads(raw)
        assert result["created"] == datetime(2026, 3, 13, 14, 30, 0)

    def test_parse_date_string(self) -> None:
        raw = '{"day": "2026-03-13"}'
        result = safe_loads(raw)
        assert result["day"] == date(2026, 3, 13)

    def test_parse_datetime_with_timezone(self) -> None:
        raw = '{"ts": "2026-03-13T14:30:00+02:00"}'
        result = safe_loads(raw)
        assert isinstance(result["ts"], datetime)
        assert result["ts"].tzinfo is not None

    def test_parse_datetime_with_fractional_seconds(self) -> None:
        raw = '{"ts": "2026-03-13T14:30:00.123456"}'
        result = safe_loads(raw)
        assert isinstance(result["ts"], datetime)
        assert result["ts"].microsecond == 123456

    def test_parse_decimal_from_float(self) -> None:
        raw = '{"price": 19.99}'
        result = safe_loads(raw)
        assert isinstance(result["price"], Decimal)
        assert result["price"] == Decimal("19.99")

    def test_parse_decimal_from_string(self) -> None:
        raw = '{"amount": "99.95"}'
        result = safe_loads(raw)
        assert isinstance(result["amount"], Decimal)
        assert result["amount"] == Decimal("99.95")

    def test_no_parse_dates(self) -> None:
        raw = '{"created": "2026-03-13T14:30:00"}'
        result = safe_loads(raw, parse_dates=False)
        assert result["created"] == "2026-03-13T14:30:00"

    def test_no_parse_decimals(self) -> None:
        raw = '{"price": 19.99}'
        result = safe_loads(raw, parse_decimals=False)
        assert isinstance(result["price"], float)

    def test_no_parsing_at_all(self) -> None:
        raw = '{"ts": "2026-01-01T00:00:00", "price": 9.99}'
        result = safe_loads(raw, parse_dates=False, parse_decimals=False)
        assert isinstance(result["ts"], str)
        assert isinstance(result["price"], float)

    def test_nested_parsing(self) -> None:
        raw = '{"order": {"created": "2026-01-15", "items": [{"price": 5.50}]}}'
        result = safe_loads(raw)
        assert result["order"]["created"] == date(2026, 1, 15)
        assert isinstance(result["order"]["items"][0]["price"], Decimal)

    def test_non_date_strings_unchanged(self) -> None:
        raw = '{"name": "hello", "desc": "not-a-date"}'
        result = safe_loads(raw)
        assert result["name"] == "hello"
        assert result["desc"] == "not-a-date"

    def test_non_numeric_strings_unchanged(self) -> None:
        raw = '{"label": "abc", "code": "XY-123"}'
        result = safe_loads(raw, parse_decimals=True)
        assert result["label"] == "abc"
        assert result["code"] == "XY-123"

    def test_integers_unchanged(self) -> None:
        raw = '{"count": 42}'
        result = safe_loads(raw)
        assert result["count"] == 42
        assert isinstance(result["count"], int)

    def test_booleans_and_null_unchanged(self) -> None:
        raw = '{"flag": true, "empty": null}'
        result = safe_loads(raw)
        assert result["flag"] is True
        assert result["empty"] is None

    def test_round_trip_with_safe_loads(self) -> None:
        original = {
            "created": datetime(2026, 3, 13, 14, 30, 0),
            "price": Decimal("19.99"),
            "name": "test",
        }
        json_str = dumps(original)
        restored = safe_loads(json_str)
        assert restored["created"] == original["created"]
        assert restored["name"] == original["name"]

    def test_safe_loads_with_bytes(self) -> None:
        raw = b'{"day": "2026-03-13"}'
        result = safe_loads(raw)
        assert result["day"] == date(2026, 3, 13)


# Import Any for type annotations in test classes
from typing import Any
