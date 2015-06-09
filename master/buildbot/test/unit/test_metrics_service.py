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
from buildbot.metrics.metrics_service import MetricsStorageBase
from buildbot.metrics.metrics_service import InfluxStorageService
from buildbot.steps import master
from buildbot.status.results import SUCCESS
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
        self.checkEqual(self.master.config)

    @defer.inlineCallbacks
    def test_reconfigure_with_fake_service(self):
        # First, configure with an empty service
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)
        self.checkEqual(self.master.config)

        # Now, reconfigure with a FakeMetricsStorageService.
        self.master.config.metricsServices = [fakemetrics.FakeMetricsStorageService()]
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)
        self.checkEqual(self.master.config)

        # unset it, see it stop
        self.master.config.metricsServices = []
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)
        self.checkEqual(self.master.config)

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
            raise unittest.SkipTest("Skipping unit test of InfluxStorageService because "
                                    "you don't have the influxdb module in your system")

        self.master.config.metricsServices = [InfluxStorageService(
            "fake_url", "fake_port", "fake_user", "fake_password", "fake_db", "fake_metrics",
        )]
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)
        self.checkEqual(self.master.config)

    @defer.inlineCallbacks
    def test_bad_configuration(self):
        # First, configure with an emnpty service
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)
        self.checkEqual(self.master.config)

        # Now, reconfigure with a bad configuration.
        self.master.config.metricsServices = [mock.Mock()]
        yield self.assertRaises(TypeError,
            self.master.metrics_service.reconfigServiceWithBuildbotConfig, self.master.config)


    def checkEqual(self, new_config):
        # Check whether the new_config was set in reconfigServiceWithBuildbotConfig
        newMerticsStorageServices = [s for s in new_config.metricsServices
                                     if isinstance(s, MetricsStorageBase)]
        registeredStorageServices = \
        [s for s in self.master.metrics_service.registeredStorageServices
         if isinstance(s, MetricsStorageBase)]
        for s in newMerticsStorageServices:
            if s not in registeredStorageServices:
                raise AssertionError("reconfigServiceWithBuildbotConfig failed."
                                     "Not all storage services registered.")


class TestMetricsServicesYieldValue(TestMetricsServicesBase):

    @defer.inlineCallbacks
    def test_reconfigure_without_conf(self):
        fake_db_service = fakemetrics.FakeMetricsStorageService()
        self.master.config.metricsServices = [fake_db_service]
        yield self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)
        name = "metrics name"
        value = "value"
        context = {"builder_name": "TestBuilder"}
        yield self.master.metrics_service.postMetricsValue(name, value, context)

        self.assertEqual([
            ("metrics name", "value", {"builder_name": "TestBuilder"}
        )], fake_db_service.stored_data)


class TestMetricsServicesCallFromAStep(steps.BuildStepMixin, unittest.TestCase):
    """
    test the metrics service from a fake step
    """
    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    @defer.inlineCallbacks
    def test_expose_property_from_step(self):
        # this step tests both the property being exposed and
        # also the postMetrics method
        fake_storage_service = fakemetrics.FakeMetricsStorageService()
        step = fakemetrics.FakeBuildStep()
        self.setupStep(step)
        self.expectOutcome(SUCCESS)

        self.master.config.metricsServices = [fake_storage_service]
        self.master.metrics_service.reconfigServiceWithBuildbotConfig(self.master.config)

        yield self.runStep()

        self.master.metrics_service.postProperties(self.properties, "TestBuilder")

        self.assertEqual([
            ("test", 10, {"builder_name": "TestBuilder"})
        ], fake_storage_service.stored_data)
