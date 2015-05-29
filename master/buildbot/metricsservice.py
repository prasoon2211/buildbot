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


class MetricsService(object):
    """
    A middleware for passing on metrics data to InfluxDBService
    """
    def __init__(self, props):
        self.influxServices = []
        self.props = props
        self.masterConfig = config.MasterConfig()

        # for other types of storage services
        # self.otherServices = []
        # import ipdb;ipdb.set_trace()
        for service in self.masterConfig.metricsServices:
            if isinstance(service, InfluxDBService):
                self.influxServices.append(service)
            # if isinstance(service, OtherService):
            #     self.otherServices.append(service)

    def postDataToStorage(self, propname, propvalue):
        # post to each of the storage services
        # import ipdb;ipdb.set_trace()
        for influxService in self.influxServices:
            serviceMetrics = influxService.metrics
            buildername = self.props.getProperty('buildername')
            for serviceMetric in serviceMetrics:
                if buildername == serviceMetric[0] and \
                   propname == serviceMetric[1]:
                    data = {}
                    data['name'] = buildername + '-' + propname
                    data['fields'] = {
                        "property_name": propname,
                        "property_value": propvalue
                    }
                    data['tags'] = {
                        "buildername": buildername,
                    }
                    try:
                        data['tags'].update(serviceMetric[2])
                    except IndexError:
                        pass
                    points = [data]
                    influxService.client.write_points(points)


class InfluxDBService(object):
    """
    Delegates data to InfluxDB
    """
    def __init__(self, url, port, user, password, db, metrics):
        self.url = url
        self.port = port
        self.user = user
        self.password = password
        self.db = db

        self.metrics = metrics

        try:
            from influxdb import InfluxDBClient
        except:
            pass
        self.client = InfluxDBClient(self.url, self.port, self.user,
                                     self.password, self.db)
