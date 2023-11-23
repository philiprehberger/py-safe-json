# Changelog

## 0.2.0 (2026-03-28)

- Add custom type encoder registration via `register_encoder(type_class, handler_fn)` and `clear_encoders()`
- Add circular reference detection with `dumps(obj, detect_cycles=True)` and `CircularReferenceError`
- Add `safe_loads(json_string, parse_dates=True, parse_decimals=True)` for automatic ISO date and Decimal parsing

## 0.1.5 (2026-03-22)

- Add pytest and mypy configuration to pyproject.toml

## 0.1.3

- Add Development section to README

## 0.1.0 (2026-03-13)

- Initial release
- SafeJsonEncoder for datetime, date, Decimal, UUID, dataclass, set, frozenset, bytes, Enum, Path
- `dumps()` and `loads()` convenience functions
- Option to serialize Decimal as string
