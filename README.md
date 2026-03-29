# philiprehberger-safe-json

[![Tests](https://github.com/philiprehberger/py-safe-json/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-safe-json/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-safe-json.svg)](https://pypi.org/project/philiprehberger-safe-json/)
[![GitHub release](https://img.shields.io/github/v/release/philiprehberger/py-safe-json)](https://github.com/philiprehberger/py-safe-json/releases)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-safe-json)](https://github.com/philiprehberger/py-safe-json/commits/main)
[![License](https://img.shields.io/github/license/philiprehberger/py-safe-json)](LICENSE)
[![Bug Reports](https://img.shields.io/github/issues/philiprehberger/py-safe-json/bug)](https://github.com/philiprehberger/py-safe-json/issues?q=is%3Aissue+is%3Aopen+label%3Abug)
[![Feature Requests](https://img.shields.io/github/issues/philiprehberger/py-safe-json/enhancement)](https://github.com/philiprehberger/py-safe-json/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
[![Sponsor](https://img.shields.io/badge/sponsor-GitHub%20Sponsors-ec6cb9)](https://github.com/sponsors/philiprehberger)

JSON encoder that handles datetime, Decimal, UUID, dataclasses, and sets without crashing.

## Installation

```bash
pip install philiprehberger-safe-json
```

## Usage

```python
from philiprehberger_safe_json import dumps, loads

data = {
    "created": datetime(2026, 3, 13, 12, 0, 0),
    "price": Decimal("19.99"),
    "id": UUID("12345678-1234-5678-1234-567812345678"),
    "tags": {"beta", "release"},
}

json_string = dumps(data)
parsed = loads(json_string)
```

### Datetime and Date

```python
from datetime import datetime, date
from philiprehberger_safe_json import dumps

dumps({"timestamp": datetime(2026, 1, 15, 9, 30, 0)})
# '{"timestamp": "2026-01-15T09:30:00"}'

dumps({"day": date(2026, 1, 15)})
# '{"day": "2026-01-15"}'
```

### Decimal

```python
from decimal import Decimal
from philiprehberger_safe_json import dumps

dumps({"price": Decimal("9.99")})
# '{"price": 9.99}'

dumps({"price": Decimal("9.99")}, decimal_as_string=True)
# '{"price": "9.99"}'
```

### UUID

```python
from uuid import UUID
from philiprehberger_safe_json import dumps

dumps({"id": UUID("abcdef01-2345-6789-abcd-ef0123456789")})
# '{"id": "abcdef01-2345-6789-abcd-ef0123456789"}'
```

### Dataclasses

```python
from dataclasses import dataclass
from philiprehberger_safe_json import dumps

@dataclass
class User:
    name: str
    age: int

dumps({"user": User(name="Alice", age=30)})
# '{"user": {"name": "Alice", "age": 30}}'
```

### Sets and Frozensets

```python
from philiprehberger_safe_json import dumps

dumps({"tags": {"c", "a", "b"}})
# '{"tags": ["a", "b", "c"]}'
```

### Custom Type Encoders

```python
from philiprehberger_safe_json import dumps, register_encoder

class Money:
    def __init__(self, amount: int, currency: str) -> None:
        self.amount = amount
        self.currency = currency

register_encoder(Money, lambda m: {"amount": m.amount, "currency": m.currency})

dumps({"payment": Money(1000, "USD")})
# '{"payment": {"amount": 1000, "currency": "USD"}}'
```

### Circular Reference Detection

```python
from philiprehberger_safe_json import dumps, CircularReferenceError

data = {"key": "value"}
data["self"] = data  # circular reference

dumps(data, detect_cycles=True)
# Raises CircularReferenceError
```

### Safe Loads with Auto-Parsing

```python
from philiprehberger_safe_json import safe_loads

result = safe_loads('{"created": "2026-03-13T14:30:00", "price": 19.99}')
# result["created"] -> datetime(2026, 3, 13, 14, 30, 0)
# result["price"] -> Decimal("19.99")

result = safe_loads('{"day": "2026-03-13"}')
# result["day"] -> date(2026, 3, 13)
```

### Using SafeJsonEncoder Directly

```python
import json
from philiprehberger_safe_json import SafeJsonEncoder

json.dumps({"key": some_value}, cls=SafeJsonEncoder)
```

## API

| Function / Class | Description |
|------------------|-------------|
| `SafeJsonEncoder` | `json.JSONEncoder` subclass that handles datetime, date, Decimal, UUID, dataclass, set, frozenset, bytes, Enum, and Path |
| `SafeJsonEncoder.decimal_as_string` | Class attribute; when `True`, Decimal values serialize as strings instead of floats (default: `False`) |
| `dumps(obj, *, decimal_as_string=False, detect_cycles=False, **kwargs)` | Serialize to JSON string using SafeJsonEncoder. Set `detect_cycles=True` to raise `CircularReferenceError` on circular refs |
| `loads(s, **kwargs)` | Deserialize a JSON string. Pass-through to `json.loads` for API symmetry |
| `safe_loads(s, *, parse_dates=True, parse_decimals=True, **kwargs)` | Deserialize with auto-parsing of ISO date strings to datetime/date and numeric values to Decimal |
| `register_encoder(type_class, handler_fn)` | Register a custom encoder for a specific type without subclassing |
| `clear_encoders()` | Remove all registered custom encoders |
| `CircularReferenceError` | Exception raised when a circular reference is detected during serialization |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Support

If you find this package useful, consider giving it a star on GitHub — it helps motivate continued maintenance and development.

[![LinkedIn](https://img.shields.io/badge/Philip%20Rehberger-LinkedIn-0A66C2?logo=linkedin)](https://www.linkedin.com/in/philiprehberger)
[![More packages](https://img.shields.io/badge/more-open%20source%20packages-blue)](https://philiprehberger.com/open-source-packages)

## License

[MIT](LICENSE)
