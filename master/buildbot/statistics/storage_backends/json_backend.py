# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

import json
import os

from os.path import expanduser
from twisted.python import log

from buildbot.statistics.storage_backends.base import StatsStorageBase

# change it later on
DEFAULT_BASE_DIR = expanduser("~") + os.sep + "buildbot"


class JSONStorageBackend(StatsStorageBase):

    """
    A storage backend based on a JSON store.
    """

    def __init__(self, captures, name="JSONStorageBackend", base_dir=None):

        self.captures = captures
        self.name = name
        self._base_dir = base_dir if base_dir else DEFAULT_BASE_DIR

        # if base_dir does not exist, create it
        if not os.path.isdir(self._base_dir):
            os.makedirs(self._base_dir)

    def thd_postStatsValue(self, post_data, series_name, context=None):
        file_location = self._base_dir + os.sep + series_name
        json_file = open(file_location, 'r+')
        data = json_file.read()

        if data:
            # data is a list of dictionaries that hold post_data and context
            data = json.loads(data)
        else:
            data = []

        new_point = {
            'post_data': post_data,
        }

        if context:
            new_point['context'] = context

        data.append(new_point)
        log.msg("Writing %s to json backend" % new_point)

        json_file.seek(0)
        json_file.write(json.dumps(data))
        json_file.close()
