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
# License.
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
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****
"""
Bootstrap file server
"""
import os
import mimetypes
from hashlib import md5
from wsgiref.simple_server import make_server

# where the served files are located ?
_DIR = '.'


def application(environ, start_response):
    if_none_match = environ.get('HTTP_IF_NONE_MATCH', '')
    path = environ['PATH_INFO']
    path = path.lstrip('/')

    if path.startswith('.') or '/' in path:
        # looks like a bad path -- or a potential security thread
        status = '400 Bad Request'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return "Invalid Request"

    path = os.path.join(_DIR, path)

    if not os.path.isfile(path):
        # unknown file
        status = '404 Not Found'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return "File not found"

    # we're good, let's look at the file age
    etag = '"%s"' % md5(str(os.stat(path).st_mtime)).hexdigest()
    if etag == if_none_match:
        # same file
        status = '412 Precondition failed'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return ''

    content_type = mimetypes.guess_type(path)
    status = '200 OK'
    headers = [('Content-type', content_type[0]),
               ('ETag', etag)]

    start_response(status, headers)

    with open(path) as f:
        content = f.read()

    return content


if __name__ == '__main__':
    httpd = make_server('', 5000, application)
    print "Listening on port 5000...."
    httpd.serve_forever()
