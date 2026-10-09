import os
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:  # pragma: no cover
        raise ValueError(f"Environment variable {name} must be an integer: {value!r}") from exc


@dataclass(slots=True)
class Settings:
    api_base_url: str = os.getenv("PET_HOSPITAL_API_BASE_URL", "http://127.0.0.1:8080")
    transport: str = os.getenv("MCP_TRANSPORT", "stdio")
    host: str = os.getenv("MCP_HOST", "127.0.0.1")
    port: int = _get_int("MCP_PORT", 8000)

    @property
    def api_base_url_normalized(self) -> str:
        return self.api_base_url.rstrip("/")
