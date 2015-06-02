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

from twisted.internet import defer
from twisted.internet import threads
from twisted.python import log

from buildbot import config
from buildbot.util import service


def deferToThread(f):
    '''
    Run a synchronous method that potentially can take lot of time into a deferred thread, so this
    will not block the main reactor. Use it when you want to issue network request with a non
    twisted library.
    '''
    def decorated(*args, **kwargs):
        return threads.deferToThread(f, *args, **kwargs)
    return decorated


class MetricsService(service.ReconfigurableServiceMixin, service.AsyncMultiService):
    """
    A middleware for passing on metrics data to all storage backends.
    """
    def __init__(self, master):
        service.AsyncMultiService.__init__(self)
        self.setName('metricsService')
        log.msg("Creating MetricsService")
        self.master = master
        self.registeredDbServices = []

    def reconfigServiceWithBuildbotConfig(self, new_config):
        log.msg("Reconfiguring MetricsService with config: {!r}".format(new_config))

        # To remove earlier used services when reconfig happens
        self.registeredDbServices = []
        for svc in new_config.metricsServices:
            if not isinstance(svc, DBServiceBase):
                raise TypeError("Invalid type of metrics storage service {0!r}. "
                                "Should be of type DBServiceBase, "
                                "is: {0!r}".format(type(DBServiceBase)))
            self.registeredDbServices.append(svc)

        return service.ReconfigurableServiceMixin.reconfigServiceWithBuildbotConfig(self,
                                                                                    new_config)

    @defer.inlineCallbacks
    def postMetricsValue(self, name, value, context):
        """
        Post to each of the storage services
        name: name of the metrics that has been created by the step
        value: value of this metrics
        context: dictionary with contextual information (TBD), such as:
           - step_name
           - builder_name (Required)
           - builder_id
           - ...
        """
        if not context.has_key('builder_name'):
            raise KeyError("The method parameter `context` does not have "
                           "key 'builder_name'")
        for registeredService in self.registeredDbServices:
            yield registeredService.postMetricsValue(name, value, context)


class DBServiceBase(object):
    """
    Base class for sub service responsible for passing on metrics data to a Metrics Storage
    """
    def postMetricsValue(self, name, value, context):
        return defer.succeed(None)


class InfluxDBService(DBServiceBase):
    """
    Delegates data to InfluxDB
    """
    def __init__(self, url, port, user, password, db, metrics, name=None):
        self.url = url
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        if not name:
            self.name = "InfluxDBService"
        else:
            self.name = name

        self.metrics = metrics
        self.inited = False
        try:
            from influxdb import InfluxDBClient
            self.client = InfluxDBClient(self.url, self.port, self.user,
                                         self.password, self.db)
            self.inited = True
        except:
            raise NotImplementedError

    @deferToThread
    def postMetricsValue(self, name, value, context):
        if not self.inited:
            log.err("Service {} not initialized".format(self.name))
            return
        log.msg("Sending data to InfluxDB")
        log.msg("name: {!r}".format(name))
        log.msg("value: {!r}".format(value))
        log.msg("context: {!r}".format(context))

        # necessarily set. See MetricsService.postMetricsValue
        builder_name = context['builder_name']
        data = {}
        data['name'] = builder_name + '-' + name
        data['fields'] = {
            "name": name,
            "value": value
        }
        data['tags'] = context
        points = [data]
        self.client.write_points(points)
