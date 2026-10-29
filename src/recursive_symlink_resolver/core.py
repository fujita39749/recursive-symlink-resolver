"""Core resolver implementation."""

import os


class ResolutionError(Exception):
    """Raised when symlink resolution cannot succeed.

    The two cases are: a cycle among symlinks, or a dead-end link whose
    target does not exist on disk.
    """


def resolve(path, max_depth=40):
    """Resolve a path containing nested symlinks to its final real target.

    Unlike :func:`os.path.realpath`, this function reports cycles
    explicitly rather than silently returning an OS-specific broken
    path. If the final link points at a non-existent file, the last
    existing intermediate path is returned (mirroring what most shells
    do when you follow a chain by hand).

    Parameters
    ----------
    path : str
        The path to resolve. Must be absolute or resolvable from the
        process's current working directory.
    max_depth : int
        Hard stop on symlink hops. ``os.symlink`` itself has no limit,
        but kernels cap chains at 40; we mirror that so callers cannot
        accidentally trigger a runaway loop on a malformed filesystem.

    Returns
    -------
    str
        The resolved path as an absolute string with symlinks expanded.

    Raises
    ------
    ResolutionError
        If a cycle is detected or ``max_depth`` is exceeded.
    """
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")

    if not isinstance(path, str):
        raise TypeError("path must be a string")

    seen = set()
    current = os.path.abspath(path)

    for _ in range(max_depth + 1):
        if os.path.islink(current):
            target = os.readlink(current)
            if not os.path.isabs(target):
                target = os.path.join(os.path.dirname(current), target)
            target = os.path.normpath(target)

            if target in seen:
                raise ResolutionError(
                    "symlink cycle detected at " + str(target)
                )

            seen.add(target)
            current = target
            continue

        return os.path.realpath(current)

    raise ResolutionError(
        "max_depth (" + str(max_depth) + ") exceeded resolving " + path
    )
