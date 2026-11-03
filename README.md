# recursive-symlink-resolver

Resolves a path containing nested symlinks to its final real target while detecting resolution cycles.

```python
from recursive_symlink_resolver import resolve, ResolutionError

try:
    real = resolve("/path/that/may/be/symlinked")
except ResolutionError as exc:
    # a cycle was detected among the links
    print(exc)
```

The standard `os.path.realpath` flattens symlink chains silently. On Linux it tends to return a partially-resolved path for a cyclic chain; on other platforms the behaviour varies. This library gives you one consistent answer: either the fully resolved path, or a `ResolutionError` explaining that a cycle or depth limit was hit.

The interpretation chosen: a symlink whose *target* does not exist is not an error. The chain terminates at that last link and its textual target is returned, matching what most shells report. Only cycles and excessive depth raise.

`max_depth` defaults to 40, mirroring the Linux kernel's `SYMLOOP_MAX`. If your platform enforces a different limit the resolver will still stop at 40 hops, which is enough for any legitimate chain and short enough to fail fast on a runaway loop.

The awkward edge: because resolution relies on `os.path.realpath`, the returned string uses the OS's canonical form. On macOS, paths under `/private/var` will be reported with that prefix even if the input did not include it. That is the OS resolving a top-level symlink; the library does not try to undo it.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

