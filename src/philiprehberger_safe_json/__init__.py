"""JSON encoder that handles datetime, Decimal, UUID, dataclasses, and sets without crashing."""

from __future__ import annotations

import base64
import dataclasses
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import PurePath
from typing import Any, Callable

from uuid import UUID

__all__ = [
    "SafeJsonEncoder",
    "dumps",
    "loads",
    "safe_loads",
    "register_encoder",
    "clear_encoders",
    "CircularReferenceError",
]

# ISO 8601 datetime pattern: YYYY-MM-DDTHH:MM:SS with optional fractional seconds and timezone
_ISO_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$"
)
# ISO 8601 date pattern: YYYY-MM-DD (but not datetime)
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Registry for custom type encoders: maps type -> handler function
_custom_encoders: dict[type, Callable[[Any], Any]] = {}


class CircularReferenceError(ValueError):
    """Raised when a circular reference is detected during JSON serialization."""

    def __init__(self, message: str = "Circular reference detected during JSON serialization") -> None:
        super().__init__(message)


def register_encoder(type_class: type, handler_fn: Callable[[Any], Any]) -> None:
    """Register a custom encoder for a specific type.

    The handler function receives an instance of the type and must return
    a JSON-serializable value.

    Args:
        type_class: The type to register an encoder for.
        handler_fn: A callable that converts an instance of type_class to
            a JSON-serializable value.
    """
    _custom_encoders[type_class] = handler_fn


def clear_encoders() -> None:
    """Remove all registered custom encoders."""
    _custom_encoders.clear()


class SafeJsonEncoder(json.JSONEncoder):
    """JSON encoder with support for common Python types."""

    decimal_as_string: bool = False

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, date):
            return o.isoformat()
        if isinstance(o, Decimal):
            return str(o) if self.decimal_as_string else float(o)
        if isinstance(o, UUID):
            return str(o)
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        if isinstance(o, (set, frozenset)):
            return sorted(o, key=str)
        if isinstance(o, bytes):
            return base64.b64encode(o).decode("ascii")
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, PurePath):
            return str(o)

        # Check custom registered encoders
        for type_class, handler_fn in _custom_encoders.items():
            if isinstance(o, type_class):
                return handler_fn(o)

        return super().default(o)


def _check_circular(obj: Any, seen: set[int] | None = None) -> None:
    """Recursively check for circular references in an object graph.

    Raises CircularReferenceError if a circular reference is detected.
    """
    if seen is None:
        seen = set()

    if isinstance(obj, dict):
        obj_id = id(obj)
        if obj_id in seen:
            raise CircularReferenceError()
        seen.add(obj_id)
        for value in obj.values():
            _check_circular(value, seen)
        seen.discard(obj_id)
    elif isinstance(obj, (list, tuple)):
        obj_id = id(obj)
        if obj_id in seen:
            raise CircularReferenceError()
        seen.add(obj_id)
        for item in obj:
            _check_circular(item, seen)
        seen.discard(obj_id)
    elif isinstance(obj, (set, frozenset)):
        obj_id = id(obj)
        if obj_id in seen:
            raise CircularReferenceError()
        seen.add(obj_id)
        for item in obj:
            _check_circular(item, seen)
        seen.discard(obj_id)
    elif dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        obj_id = id(obj)
        if obj_id in seen:
            raise CircularReferenceError()
        seen.add(obj_id)
        for field in dataclasses.fields(obj):
            _check_circular(getattr(obj, field.name), seen)
        seen.discard(obj_id)


def _make_encoder(decimal_as_string: bool = False) -> type[SafeJsonEncoder]:
    """Create an encoder class with the given options."""

    class _Encoder(SafeJsonEncoder):
        pass

    _Encoder.decimal_as_string = decimal_as_string
    return _Encoder


def dumps(
    obj: Any,
    *,
    decimal_as_string: bool = False,
    detect_cycles: bool = False,
    **kwargs: Any,
) -> str:
    """Serialize obj to a JSON string using SafeJsonEncoder.

    Args:
        obj: The object to serialize.
        decimal_as_string: If True, Decimal values are serialized as strings
            instead of floats.
        detect_cycles: If True, checks for circular references before
            serialization and raises CircularReferenceError if found.
        **kwargs: Additional keyword arguments passed to json.dumps.

    Returns:
        A JSON string.

    Raises:
        CircularReferenceError: If detect_cycles is True and a circular
            reference is found.
    """
    if detect_cycles:
        _check_circular(obj)
    return json.dumps(obj, cls=_make_encoder(decimal_as_string), **kwargs)


def loads(s: str | bytes, **kwargs: Any) -> Any:
    """Deserialize a JSON string. Pass-through to json.loads for symmetry."""
    return json.loads(s, **kwargs)


def _parse_value(value: Any, *, parse_dates: bool, parse_decimals: bool) -> Any:
    """Recursively parse values, converting strings to dates/decimals as requested."""
    if isinstance(value, dict):
        return {
            k: _parse_value(v, parse_dates=parse_dates, parse_decimals=parse_decimals)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [
            _parse_value(item, parse_dates=parse_dates, parse_decimals=parse_decimals)
            for item in value
        ]
    if isinstance(value, str):
        if parse_dates:
            if _ISO_DATETIME_RE.match(value):
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    pass
            elif _ISO_DATE_RE.match(value):
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    pass
        if parse_decimals and isinstance(value, str):
            # Only parse strings that look like numbers (not dates or other strings)
            # Must not have already been parsed as a date
            if not parse_dates or (not _ISO_DATETIME_RE.match(value) and not _ISO_DATE_RE.match(value)):
                try:
                    return Decimal(value)
                except InvalidOperation:
                    pass
    if isinstance(value, float) and parse_decimals:
        return Decimal(str(value))
    return value


def safe_loads(
    s: str | bytes,
    *,
    parse_dates: bool = True,
    parse_decimals: bool = True,
    **kwargs: Any,
) -> Any:
    """Deserialize a JSON string with automatic type parsing.

    Extends json.loads with optional parsing of ISO date strings back to
    datetime/date objects and numeric values to Decimal.

    Args:
        s: The JSON string to deserialize.
        parse_dates: If True, ISO 8601 date/datetime strings are parsed
            back to datetime.date or datetime.datetime objects.
        parse_decimals: If True, numeric string values are parsed to Decimal,
            and float values are converted to Decimal for precision.
        **kwargs: Additional keyword arguments passed to json.loads.

    Returns:
        The deserialized Python object with parsed types.
    """
    raw = json.loads(s, **kwargs)
    if not parse_dates and not parse_decimals:
        return raw
    return _parse_value(raw, parse_dates=parse_dates, parse_decimals=parse_decimals)
