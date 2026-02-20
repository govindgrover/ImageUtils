import re

def _parse_version(version_str: str) -> tuple[int, ...]:
    parts = tuple(int(piece) for piece in re.findall(r"\d+", version_str or ""))
    return parts if parts else (0,)

def _is_newer_version(remote: str, local: str) -> bool:
    remote_parts = _parse_version(remote)
    local_parts = _parse_version(local)
    max_length = max(len(remote_parts), len(local_parts))
    remote_parts += (0,) * (max_length - len(remote_parts))
    local_parts += (0,) * (max_length - len(local_parts))
    return remote_parts > local_parts

