import os


def required_environment(name: str) -> str:
    """Return a non-empty environment setting or stop an unsafe release."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment setting: {name}")
    return value
