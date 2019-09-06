from __future__ import unicode_literals

import os
import re
import shutil
import sys

from rbtools.utils import checks, filesystem
from rbtools.utils.aliases import replace_arguments
from rbtools.utils.filesystem import (cleanup_tempfiles, make_empty_files,
                                      make_tempdir, make_tempfile)
from rbtools.utils.process import execute
from rbtools.utils.testbase import RBTestBase


class ChecksTests(RBTestBase):
    """Unit tests for rbtools.utils.checks."""

    def test_check_install(self):
        """Testing check_install"""
        self.assertTrue(checks.check_install([sys.executable, ' --version']))
        self.assertFalse(checks.check_install([self.gen_uuid()]))

    def test_is_valid_version(self):
        """Testing is_valid_version"""
        self.assertTrue(checks.is_valid_version((1, 0, 0), (1, 0, 0)))
        self.assertTrue(checks.is_valid_version((1, 1, 0), (1, 0, 0)))
        self.assertTrue(checks.is_valid_version((1, 0, 1), (1, 0, 0)))
        self.assertTrue(checks.is_valid_version((1, 1, 0), (1, 1, 0)))
        self.assertTrue(checks.is_valid_version((1, 1, 1), (1, 1, 0)))
        self.assertTrue(checks.is_valid_version((1, 1, 1), (1, 1, 1)))

        self.assertFalse(checks.is_valid_version((0, 9, 9), (1, 0, 0)))
        self.assertFalse(checks.is_valid_version((1, 0, 9), (1, 1, 0)))
        self.assertFalse(checks.is_valid_version((1, 1, 0), (1, 1, 1)))


class FilesystemTests(RBTestBase):
    """Unit tests for rbtools.utils.filesystem."""

    def test_make_tempfile(self):
        """Testing make_tempfile"""
        filename = make_tempfile()
        self.assertIn(filename, filesystem.tempfiles)

        self.assertTrue(os.path.isfile(filename))
        self.assertTrue(os.path.basename(filename).startswith('rbtools.'))
        self.assertEqual(os.stat(filename).st_uid, os.geteuid())
        self.assertTrue(os.access(filename, os.R_OK | os.W_OK))

    def test_make_tempfile_with_prefix(self):
        """Testing make_tempfile with prefix"""
        filename = make_tempfile(prefix='supertest-')

        self.assertIn(filename, filesystem.tempfiles)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue(os.path.basename(filename).startswith('supertest-'))
        self.assertEqual(os.stat(filename).st_uid, os.geteuid())
        self.assertTrue(os.access(filename, os.R_OK | os.W_OK))

    def test_make_tempfile_with_suffix(self):
        """Testing make_tempfile with suffix"""
        filename = make_tempfile(suffix='.xyz')

        self.assertIn(filename, filesystem.tempfiles)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue(os.path.basename(filename).startswith('rbtools.'))
        self.assertTrue(os.path.basename(filename).endswith('.xyz'))
        self.assertEqual(os.stat(filename).st_uid, os.geteuid())
        self.assertTrue(os.access(filename, os.R_OK | os.W_OK))

    def test_make_tempfile_with_filename(self):
        """Testing make_tempfile with filename"""
        filename = make_tempfile(filename='TEST123')

        self.assertIn(filename, filesystem.tempfiles)
        self.assertEqual(os.path.basename(filename), 'TEST123')
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue(os.access(filename, os.R_OK | os.W_OK))
        self.assertEqual(os.stat(filename).st_uid, os.geteuid())

        parent_dir = os.path.dirname(filename)
        self.assertIn(parent_dir, filesystem.tempdirs)
        self.assertTrue(os.access(parent_dir, os.R_OK | os.W_OK | os.X_OK))
        self.assertEqual(os.stat(parent_dir).st_uid, os.geteuid())

    def test_make_empty_files(self):
        """Testing make_empty_files"""
        # Use make_tempdir to get a unique directory name
        tmpdir = make_tempdir()
        self.assertTrue(os.path.isdir(tmpdir))
        cleanup_tempfiles()

        fname = os.path.join(tmpdir, 'file')
        make_empty_files([fname])
        self.assertTrue(os.path.isdir(tmpdir))
        self.assertTrue(os.path.isfile(fname))
        self.assertEqual(os.stat(fname).st_uid, os.geteuid())
        self.assertTrue(os.access(fname, os.R_OK | os.W_OK))

        shutil.rmtree(tmpdir, ignore_errors=True)


class ProcessTests(RBTestBase):
    """Unit tests for rbtools.utils.process."""

    def test_execute(self):
        """Testing execute"""
        self.assertTrue(re.match('.*?%d.%d.%d' % sys.version_info[:3],
                        execute([sys.executable, '-V'])))


class AliasTests(RBTestBase):
    """Tests for rbtools.utils.aliases."""

    def test_replace_arguments_basic(self):
        """Testing replace_arguments with variables and arguments"""
        self.assertEqual(replace_arguments('$1', ['HEAD'], posix=True),
                         ['HEAD'])

    def test_replace_arguments_multiple(self):
        """Testing replace_arguments with multiple variables and arguments"""
        self.assertEqual(replace_arguments('$1..$2', ['a', 'b'], posix=True),
                         ['a..b'])

    def test_replace_arguments_blank(self):
        """Testing replace_arguments with variables and a missing argument"""
        self.assertEqual(replace_arguments('rbt post $1', [], posix=True),
                         ['rbt', 'post'])

    def test_replace_arguments_append(self):
        """Testing replace_arguments with no variables or arguments."""
        self.assertEqual(
            replace_arguments('echo', ['a', 'b', 'c'], posix=True),
            ['echo', 'a', 'b', 'c'])

    def test_replace_arguments_unrecognized_variables(self):
        """Testing replace_arguments with an unrecognized variable name"""
        self.assertEqual(replace_arguments('$1 $test', ['f'], posix=True),
                         ['f', '$test'])

    def test_replace_arguments_star(self):
        """Testing replace_arguments with the special $* variable"""
        self.assertEqual(replace_arguments('$*', ['a', 'b', 'c'], posix=True),
                         ['a', 'b', 'c'])

    def test_replace_arguments_star_whitespace(self):
        """Testing replace_arguments with the special $* variable with
        whitespace-containing arguments
        """
        self.assertEqual(
            replace_arguments('$*', ['a', 'b', 'c d e'], posix=True),
            ['a', 'b', 'c d e'])

    def test_replace_arguments_unescaped_non_posix(self):
        """Testing replace_arguments in non-POSIX mode does not evaluate escape
        sequences
        """
        self.assertEqual(replace_arguments(r'"$1 \\"', ['a'], posix=False),
                         [r'"a \\"'])

    def test_replace_arguments_invalid_quote(self):
        """Testing replace_arguments with invalid quotes in POSIX and non-POSIX
        mode raises an error
        """
        self.assertRaises(
            ValueError,
            lambda: replace_arguments('"foo', [], posix=True))

        self.assertRaises(
            ValueError,
            lambda: replace_arguments('"foo', [], posix=False))

    def test_replace_arguments_invalid_quote_posix(self):
        """Testing replace_arguments with escaped ending quote in non-POSIX
        mode does not escape the quote
        """
        self.assertEqual(replace_arguments('"\\"', [], posix=False),
                         ['"\\"'])

    def test_replace_arguments_invalid_quote_non_posix(self):
        """Testing replace_arguments with escaped ending quote in POSIX mode
        raises an error
        """
        self.assertRaises(
            ValueError,
            lambda: replace_arguments('"\\"', [], posix=True))

    def test_replace_arguments_quoted_non_posix(self):
        """Testing replace_arguments in non-POSIX mode with a quoted sequence
        in the command
        """
        self.assertEqual(
            replace_arguments("find . -iname '*.pyc' -delete", [],
                              posix=False),
            ['find', '.', '-iname', "'*.pyc'", '-delete'])

    def test_replace_arguments_escaped_posix(self):
        """Testing replace_arguments in POSIX mode evaluates escape sequences
        """
        self.assertEqual(
            replace_arguments(r'$1 \\ "\\" "\""', ['a'], posix=True),
            ['a', '\\', '\\', '"'])
