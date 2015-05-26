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

from buildbot import config
from influxdb import InfluxDBClient


class MetricsService(object):
    """
    A middleware for passing on metrics data to InfluxDBService
    """
    def __init__(self):
        self.influxServices = []
        # for other types of storage services
        # self.otherServices = []
        masterConfig = config.MasterConfig()

        for service in masterConfig.metricsServices:
            if isinstance(service, InfluxDBService):
                self.influxServices.append(service)

            # if isinstance(service, OtherService):
            #     self.otherServices.append(service)

    def postDataToStorage(self, data):
        points = [data]

        # post to each of the storage services
        for influxService in self.influxServices:
            metrics = influxService.metrics
            influxService.client.write_points(points)


class InfluxDBService(object):
    """
    Delegates data to InfluxDB
    """
    def __init__(self, url, port=8086, user, password, db, metrics):
        self.url = url
        self.port = port
        self.user = user
        self.password = password
        self.db = db

        self.metrics = metrics
        self.client = InfluxDBClient(self.url, self.port, self.user,
                                     self.password, self.db)
