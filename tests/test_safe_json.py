from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path, PurePosixPath
from uuid import UUID

import pytest

from philiprehberger_safe_json import SafeJsonEncoder, dumps, loads


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
