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
from buildbot.process import buildstep
from buildbot.metrics import metrics_service

class FakeMetricsStorageService(metrics_service.MetricsStorageBase):
    """
    Fake Storage service used in unit tests
    """
    def __init__(self, metrics=None):
        self.stored_data = []
        if not metrics:
            self.metrics = [metrics_service.CaptureProperty("TestBuilder",
                                                            'test')]
        else:
            self.metrics = metrics


    @defer.inlineCallbacks
    def postMetricsValue(self, name, value, context):
        self.stored_data.append((name, value, context))
        yield None


class FakeBuildStep(buildstep.BuildStep):
    """
    A fake build step to be used for testing.
    """
    def doSomething(self):
        self.setProperty("test", 10, "test")

    def start(self):
        self.doSomething()


class FakeMetricsService(metrics_service.MetricsService):
    """
    Fake MetricsService for use in fakemaster
    """
    pass
