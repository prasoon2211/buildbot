.. _metrics-service:

Metrics Service
===============

The metrics service is implemented in :mod:`buildbot.metrics.metrics_service`.
Please see :bb:cfg:`metrics-service` for more.

Metrics Service
---------------

.. py:class:: MetricsService

   An instance of this class functions as a twisted service.
   The running service is accessible everywhere in Buildbot via the :class:`BuildMaster`.
   The service is available at ``master.metrics_service``

   .. py:method:: postMetricsValue(name, value, context)

      :param name: The name of the metric being sent for storage.
      :param value: Value to be stored.
      :param context: Any other contextual information about name-value pair.
                      *Note:* The key 'builder_name' is required for the time being.
      :type context: dictionary

      This method acts as a middleware for posting data to all storage backends.

   .. py:method:: postProperties(properties, builder_name)

      :param properties: An instance of :class:`buildbot.process.Properties`
      :param builder_name: The name of the builder whose properties are being sent to
                           the storage backends.

      This method is called at the end of each build. It filters out which build
      properties to :py:meth:`postMetricsValue`

.. _storage-backend:

Storage backends
----------------

Storage backends are responsible for storing any metrics-data sent to them.
A storage backend will generally be some sort of a database-server running on a machine.
(*Note*: This machine may be different from the one running :class:`BuildMaster`)

Each storage backend has a Python frontend defined as part of :mod:`buildbot.metrics.metrics_service` to aid in posting and retrieving data by :class:`MetricsService`

Currently, only `InfluxDB <http://influxdb.com>` is supported as a storage backend.

.. py:class:: MetricsStorageBase

   A base class for all storage services

.. py:class:: InfluxStorageService

   `InfluxDB <http://influxdb.com>` is a distributed, time series database that employs a key-value pair storage system.

   This class is a frontend to the InfluxDB storage backend.
   It is available in the configuration as ``metrics_service.InfluxStorageService``
   It takes the following initialization arguments:

   * ``url``: The URL where the service is running.
   * ``port``: The port on which the service is listening.
   * ``user``: Username of a InfluxDB user.
   * ``password``: Password for ``user``.
   * ``db``: The name of database to be used.
   * ``metrics``: A list of :py:class:`CaptureProperty`. This tells which metrics are to be stored in this storage backend.
   * ``name=None``: (Optional) The name of this storage backend.

   .. py:method:: postMetricsValue(name, value, context):

      The parameters are exactly the same as :py:meth:`postMetricsValue`.

      This method is called from :py:meth:`postMetricsValue` from :class:`MetricsService`.
      It constructs a dictionary of data to be sent to InfluxDB in the proper format and
      sends the data.


Utilities
---------

.. py:class:: CaptureProperty

   A placeholder for keeping track of the properties a user wants captured as metrics.
   It takes two arguments:

   * ``builder_name``: The name of builder in which the property is recorded.
   * ``property_name``: The name of property needed to be recorded as a metric.

   It is available in the configuration as ``metrics_service.CaptureProperty``
   A list of :class:`CaptureProperty` instances is passed to a storage backend for
   filtering out the build properties that are sent to :class:`MetricsService`.
