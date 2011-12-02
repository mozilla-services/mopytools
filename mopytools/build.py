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
import os
import sys

from mopytools.util import (run, envname, update_cmd, step,
                            get_project_name, is_meta_project,
                            has_changes, is_git)


@step('Updating the repo')
def updating_repo(name, channel, specific_tags, force=False, timeout=60,
                  verbose=False):
    if not force and has_changes(timeout, verbose) and channel != 'dev':
        print('The code was changed locally, aborting!')
        print('You can use --force but all uncommited '
              'changes will be discarded.')
        sys.exit(0)

    if is_git():
        run('git submodule update')

    run(update_cmd(name, channel, specific_tags, force), timeout, verbose)


@step('Checking provided tags')
def check_tags(projects):
    tags = {}
    missing = provided = 0
    for project in projects:
        tag = envname(project)
        if tag in os.environ:
            tags[tag] = os.environ[tag]
            provided += 1
        else:
            tags[tag] = 'Not provided'
            missing += 1

    # we want all tag or no tag
    if missing > 0 and missing < len(projects):
        print("You did not specify all tags: ")
        for project, tag in tags.items():
            print('    %s: %s' % (project, tag))

        print("Also, consider using channels")
        sys.exit(1)

    return provided == len(projects) and missing == 0


@step('Checking the environ')
def get_environ_info(deps):
    name = get_project_name()
    # is the root a project itself or just a placeholder ?
    projects = list(deps)
    if not is_meta_project():
        projects.append(name)

    # check the tags
    tags = {}
    missing = provided = 0
    for project in projects:
        tag = envname(project)
        if tag in os.environ:
            tags[tag] = os.environ[tag]
            provided += 1
        else:
            tags[tag] = 'Not provided'
            missing += 1

    # we want all tag or no tag
    if missing > 0 and missing < len(projects):
        print("You did not specify all tags: ")
        for project, tag in tags.items():
            print('    %s: %s' % (project, tag))

        print("Also, consider using channels")
        sys.exit(1)

    specific_tags = provided == len(projects) and missing == 0
    return name, specific_tags
