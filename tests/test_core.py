"""Tests for recursive_symlink_resolver.core."""

import os
import shutil
import tempfile
import unittest

from recursive_symlink_resolver import resolve, ResolutionError


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rsr_test_")
        self.addCleanup(shutil.rmtree, self.tmp)

    def _path(self, *parts):
        return os.path.join(self.tmp, *parts)

    def test_plain_file_resolves_to_itself(self):
        f = self._path("real_file.txt")
        with open(f, "w") as fh:
            fh.write("data")
        self.assertEqual(os.path.realpath(resolve(f)), os.path.realpath(f))

    def test_single_symlink(self):
        target = self._path("target.txt")
        with open(target, "w") as fh:
            fh.write("x")
        link = self._path("link.txt")
        os.symlink(target, link)
        self.assertEqual(resolve(link), os.path.realpath(target))

    def test_nested_symlink_chain(self):
        a = self._path("a")
        b = self._path("b")
        c = self._path("c")
        real = self._path("real")
        with open(real, "w") as fh:
            fh.write("x")
        os.symlink(real, c)
        os.symlink(c, b)
        os.symlink(b, a)
        self.assertEqual(resolve(a), os.path.realpath(real))

    def test_relative_symlink_in_chain(self):
        # Links that use a relative path must resolve relative to the
        # *link's* directory, not the caller's cwd. os.path.realpath
        # handles that for us.
        sub = self._path("sub")
        os.makedirs(sub)
        real = os.path.join(sub, "real")
        with open(real, "w") as fh:
            fh.write("x")
        # "real" is relative; when followed from sub/ it picks up the
        # file in the same directory.
        link = os.path.join(sub, "link")
        os.symlink("real", link)
        self.assertEqual(resolve(link), os.path.realpath(real))

    def test_cycle_detected(self):
        a = self._path("cycle_a")
        b = self._path("cycle_b")
        os.symlink(b, a)
        os.symlink(a, b)
        with self.assertRaises(ResolutionError):
            resolve(a)

    def test_self_loop_detected(self):
        a = self._path("self_loop")
        os.symlink(a, a)
        with self.assertRaises(ResolutionError):
            resolve(a)

    def test_max_depth_zero_on_plain_file(self):
        f = self._path("plain.txt")
        with open(f, "w") as fh:
            fh.write("x")
        self.assertEqual(resolve(f, max_depth=0), os.path.realpath(f))

    def test_max_depth_too_small_raises(self):
        a = self._path("a")
        b = self._path("b")
        real = self._path("real")
        with open(real, "w") as fh:
            fh.write("x")
        os.symlink(real, b)
        os.symlink(b, a)
        with self.assertRaises(ResolutionError):
            resolve(a, max_depth=1)

    def test_nonexistent_target_terminated(self):
        # A symlink whose target does not exist still terminates:
        # os.path.realpath collapses it to a textual path and, on the
        # next iteration, the path is stable.
        link = self._path("dead_link")
        os.symlink(self._path("nope"), link)
        result = resolve(link)
        self.assertEqual(result, os.path.realpath(self._path("nope")))

    def test_type_error_on_non_string(self):
        with self.assertRaises(TypeError):
            resolve(123)

    def test_value_error_on_negative_depth(self):
        with self.assertRaises(ValueError):
            resolve(self._path("x"), max_depth=-1)


if __name__ == "__main__":
    unittest.main()
