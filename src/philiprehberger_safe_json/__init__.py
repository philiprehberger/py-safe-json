"""JSON encoder that handles datetime, Decimal, UUID, dataclasses, and sets without crashing."""

from __future__ import annotations

import base64
import dataclasses
import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any
from uuid import UUID

__all__ = ["SafeJsonEncoder", "dumps", "loads"]


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
        return super().default(o)


def _make_encoder(decimal_as_string: bool = False) -> type[SafeJsonEncoder]:
    """Create an encoder class with the given options."""

    class _Encoder(SafeJsonEncoder):
        pass

    _Encoder.decimal_as_string = decimal_as_string
    return _Encoder


def dumps(obj: Any, *, decimal_as_string: bool = False, **kwargs: Any) -> str:
    """Serialize obj to a JSON string using SafeJsonEncoder."""
    return json.dumps(obj, cls=_make_encoder(decimal_as_string), **kwargs)


def loads(s: str | bytes, **kwargs: Any) -> Any:
    """Deserialize a JSON string. Pass-through to json.loads for symmetry."""
    return json.loads(s, **kwargs)
