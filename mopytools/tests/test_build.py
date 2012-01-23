# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License
#
# The Original Code is Sync Server
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Tarek Ziade (tarek@mozilla.com)
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instea
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****
""" tests for mopytools.build
"""
import unittest
import subprocess
import StringIO
import ConfigParser
import sys
import tempfile
import os

from mopytools.util import get_channel_tag, tag_exists, get_options
from mopytools import util


_CMDS = {"hg tags": """\
tip                               35:7d3a88af29ec
rpm-0.5rc1                        33:51e4cfb38a04
rpm-0.4                           32:c56849d09a4c
rpm-0.4rc2                        32:51e4cfb38a04
rpm-0.4rc1                        32:51e4cfb38a04
rpm-0.3                           28:51e4cfb38a04
rpm-0.2                           9:d6f665b7d6a3""",
         "hg branches": """\
default                           35:7d3a88af29ec
feature                           34:fca8887c0991"""}


_CFG = """\
[easy_install]
index_url = http://pypi.python.org/simple

"""


class FakePopen(object):
    def __init__(self, command, *args, **kw):
        self.cmd = command
        self.stdout = StringIO.StringIO(_CMDS[command])


class ParserNoWrite(ConfigParser.ConfigParser):
    writes = []

    def write(self, cfg):
        stream = StringIO.StringIO()
        ConfigParser.ConfigParser.write(self, stream)
        stream.seek(0)
        self.writes.append((cfg, stream.read()))


class TestBuild(unittest.TestCase):

    def setUp(self):
        self.old_po = subprocess.Popen
        subprocess.Popen = FakePopen
        self.old_cp = util.ConfigParser
        util.ConfigParser = ParserNoWrite

    def tearDown(self):
        subprocess.Popen = self.old_po
        util.ConfigParser = self.old_cp

    def test_get_tag(self):
        self.assertEqual(get_channel_tag('dev'), 'default')
        self.assertEqual(get_channel_tag('prod'), 'rpm-0.4')
        self.assertEqual(get_channel_tag('stage'), 'rpm-0.5rc1')

    def test_get_tag_actually_branch(self):
        self.assertFalse('feature' in util._get_tags())
        self.assertTrue('feature' in util._get_tags(prefix=''))

    def test_tag_exists(self):
        self.assertTrue(tag_exists('tip'))
        self.assertTrue(tag_exists('rpm-0.4'))
        self.assertTrue(tag_exists('rpm-0.5rc1'))
        self.assertFalse(tag_exists('xxx'))

    def test_distutils_setup(self):
        old_argv = sys.argv[:]
        sys.argv[:] = ['whatever', 'is_done']
        try:
            options, args = get_options()
        finally:
            sys.argv[:] = old_argv

        result = ParserNoWrite.writes[-1][1]
        self.assertEquals(result, _CFG)

    def test_rmdir(self):
        from mopytools import build_rpms

        old_build_app = build_rpms.build_app
        build_rpms.build_app = lambda: None
        old_buildrpms = build_rpms._buildrpms
        build_rpms._buildrpms = lambda deps, channel, options: None
        old_argv = sys.argv[:]

        tempdir = tempfile.mkdtemp()
        with open(os.path.join(tempdir, 'xx'), 'w') as f:
            f.write('#')

        sys.argv[:] = ['', '-r', '--dist-dir', tempdir]
        old_stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        try:
            build_rpms.main()
        finally:
            sys.argv[:] = old_argv
            build_rpms.build_app = old_build_app
            build_rpms._buildrpms = old_buildrpms
            sys.stdout = old_stdout

        try:
            # let's check that the dir was removed and recreated empty
            self.assertTrue(os.path.exists(tempdir))
            self.assertEquals(len(os.listdir(tempdir)), 0)
        finally:
            os.rmdir(tempdir)

    def test_stabby(self):
        old_argv = sys.argv[:]
        sys.argv[:] = ['', 'one, ', 'two']
        old_stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        try:
            self.assertRaises(SystemExit, get_options)
        finally:
            sys.argv[:] = old_argv
            sys.stdout = old_stdout
