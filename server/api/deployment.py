import os


def required_environment(name: str) -> str:
    """Return a non-empty environment setting or stop an unsafe release."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment setting: {name}")
    return value


def split_origins(value: str) -> list[str]:
    """Normalize a whitespace-separated list of browser origins."""
    return list(
        dict.fromkeys(origin.rstrip("/") for origin in value.split() if origin)
    )
