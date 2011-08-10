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

from mopytools.build import get_tag, verify_tag


_CMDS = {"hg tags": """\
tip                               34:7d3a88af29ec
rpm-0.5rc1                        33:51e4cfb38a04
rpm-0.4                           32:c56849d09a4c
rpm-0.4rc2                        32:51e4cfb38a04
rpm-0.4rc1                        32:51e4cfb38a04
rpm-0.3                           28:51e4cfb38a04
rpm-0.2                           9:d6f665b7d6a3"""}


class FakePopen(object):
    def __init__(self, command, *args, **kw):
        self.cmd = command
        self.stdout = StringIO.StringIO(_CMDS[command])


class TestBuild(unittest.TestCase):

    def setUp(self):
        self.old = subprocess.Popen
        subprocess.Popen = FakePopen

    def tearDown(self):
        subprocess.Popen = self.old

    def test_get_tag(self):
        self.assertEqual(get_tag('dev'), 'tip')
        self.assertEqual(get_tag('prod'), 'rpm-0.4')
        self.assertEqual(get_tag('stage'), 'rpm-0.5rc1')

    def test_verify_tag(self):
        self.assertTrue(verify_tag('tip'))
        self.assertTrue(verify_tag('rpm-0.4'))
        self.assertTrue(verify_tag('rpm-0.5rc1'))
        self.assertFalse(verify_tag('xxx'))
