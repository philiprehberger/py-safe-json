# philiprehberger-safe-json

[![Tests](https://github.com/philiprehberger/py-safe-json/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-safe-json/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-safe-json.svg)](https://pypi.org/project/philiprehberger-safe-json/)
[![License](https://img.shields.io/github/license/philiprehberger/py-safe-json)](LICENSE)
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

### Bytes

```python
from philiprehberger_safe_json import dumps

dumps({"data": b"hello"})
# '{"data": "aGVsbG8="}'
```

### Enums

```python
from enum import Enum
from philiprehberger_safe_json import dumps

class Color(Enum):
    RED = "red"
    BLUE = "blue"

dumps({"color": Color.RED})
# '{"color": "red"}'
```

### Path

```python
from pathlib import Path
from philiprehberger_safe_json import dumps

dumps({"file": Path("/home/user/data.txt")})
# '{"file": "/home/user/data.txt"}'
```

### Using SafeJsonEncoder Directly

```python
import json
from philiprehberger_safe_json import SafeJsonEncoder

json.dumps({"key": some_value}, cls=SafeJsonEncoder)
```

## API

| Name | Description |
|------|-------------|
| `SafeJsonEncoder` | `json.JSONEncoder` subclass that handles datetime, date, Decimal, UUID, dataclass, set, frozenset, bytes, Enum, and Path |
| `SafeJsonEncoder.decimal_as_string` | Class attribute; when `True`, Decimal values serialize as strings instead of floats (default: `False`) |
| `dumps(obj, *, decimal_as_string=False, **kwargs)` | Serialize to JSON string using SafeJsonEncoder. Accepts all `json.dumps` keyword arguments |
| `loads(s, **kwargs)` | Deserialize a JSON string. Pass-through to `json.loads` for API symmetry |


## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
