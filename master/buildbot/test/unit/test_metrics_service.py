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

import mock

from twisted.internet import defer
from twisted.trial import unittest

from buildbot import config
from buildbot.test.fake import fakemaster
from buildbot.test.fake import fakemetrics
from buildbot.metrics.metrics_service import MetricsService
from buildbot.metrics.metrics_service import InfluxDBService
from buildbot.steps import master
from buildbot.test.util import steps


class TestMetricsServicesBase(unittest.TestCase):

    def setUp(self):
        self.master = fakemaster.make_master()
        self.master.metrics_service.startService()

    def tearDown(self):
        self.master.metrics_service.stopService()


class TestMetricsServicesConfiguration(TestMetricsServicesBase):

    @defer.inlineCallbacks
    def test_reconfigure_without_conf(self):
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)

    @defer.inlineCallbacks
    def test_reconfigure_with_fake_service(self):
        # First, configure with an empty service
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)

        # Now, reconfigure with a FakeDBService.
        self.master.config.metricsServices = [fakemetrics.FakeDBService()]
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)

        # unset it, see it stop
        self.master.config.metricsServices = []
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)

    # Smooth test of influx db service. We don't want to force people to install influxdb, so we
    # just disable this unit test if the influxdb module is not installed, using SkipTest
    @defer.inlineCallbacks
    def test_reconfigure_with_influx_service(self):
        try:
            # Try to import
            import influxdb
            # consume it somehow to please pylint
            [influxdb]
        except:
            raise unittest.SkipTest("Skipping unit test of InfluxDBService because "
                                    "you don't have the influxdb module in your system")

        self.master.config.metricsServices = [InfluxDBService(
            "fake_url", "fake_port", "fake_user", "fake_password", "fake_db", "fake_metrics",
        )]
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)


class TestMetricsServicesYieldValue(TestMetricsServicesBase):

    @defer.inlineCallbacks
    def test_reconfigure_without_conf(self):
        fake_db_service = fakemetrics.FakeDBService()
        self.master.config.metricsServices = [fake_db_service]
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)
        name = "metrics name"
        value = "value"
        context = {"builder_name": "TestBuilder"}
        yield self.master.metrics_service.postMetricsValue(name, value, context)

        self.assertEqual([
            ("metrics name", "value", {"builder_name": "TestBuilder"}
        )], fake_db_service.stored_data)


class TestMetricsServicesCallFromAStep(steps.BuildStepMixin):
    """
    test the metrics service from a fake step
    """
    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_metrics_call_from_step(self):
        fake_db_service = fakemetrics.FakeDBService()
        step = fakemetrics.FakeBuildStep(fake_db_service)
        self.setupStep(step)
        d = self.runStep()

        d.addCallback(lambda _: self.assertEqual([
            ("test", "value", {"builer_name": "TestBuilder"}
        )], fake_db_service.stored_data))

        return d
