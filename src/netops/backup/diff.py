import difflib


def generate_config_diff(
    previous_config: str,
    current_config: str,
    previous_name: str = "previous.conf",
    current_name: str = "latest.conf",
) -> str:
    """Generate a unified diff between two configurations."""

    diff = difflib.unified_diff(
        previous_config.splitlines(),
        current_config.splitlines(),
        fromfile=previous_name,
        tofile=current_name,
        lineterm="",
    )

    return "\n".join(diff)

