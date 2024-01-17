ADSBCOT's configuration parameters can be set two ways:

1. In an INI-style configuration file. (ex. ``adsbcot -c config.ini``)
2. As environment variables. (ex. ``export DEBUG=1;adsbcot``)

ADSBCOT has the following built-in configuration parameters:

* **`FEED_URL`**:
    * Default: ``file:///run/dump1090-fa/aircraft.json``

    ADS-B data source URL. Supported URL types:

    - ``file://`` The absolute local folder path to an ADS-B data file in JSON format.
    - ``http://`` The local piaware web server aircraft data JSON URL. (ex. ``http://piaware.local:8080/data/aircraft.json``)
    - ``tcp://`` A dump1090 BaseStation (SBS-1, "raw") host & port URL (ex. ``tcp://sensor.example.com:30003``).
    - ``tcp+raw://`` A dump1090 BaseStation (SBS-1, "raw") host & port URL (ex. ``tcp+raw://sensor.example.com:30003``).
    - ``tcp+beast://`` A dump1090 Beast binary mode host & port URL (ex. ``tcp+beast://sensor.example.com:30005``).

* **`POLL_INTERVAL`**:
    * Default: ``3`` seconds

    If the `FEED_URL` is of type HTTP, the period, in seconds, to poll this URL.
    
* **`ALT_UPPER`**:
    * Default: unset

    Upper Altitude Limit, geometric (GNSS / INS) altitude in feet referenced to the WGS84 ellipsoid.

* **`ALT_LOWER`**:
    * Default: unset
    
    Lower Altitude Limit, geometric (GNSS / INS) altitude in feet referenced to the WGS84 ellipsoid.

* **`KNOWN_CRAFT`**:
    * Default: unset

    CSV-style aircraft hints file for overriding callsign, icon, COT Type, etc.

* **`INCLUDE_ALL_CRAFT`**:
    * Default: ``False``

    If ``True`` and ``KNOWN_CRAFT`` is set, will forward all aircraft, including those transformed by the ``KNOWN_CRAFT`` database.

* **`INCLUDE_TISB`**:
    * Default: ``False``

    If ``True``, includes TIS-B tracks.

* **`TISB_ONLY`**:
    * Default: ``False``

    If `True`, only passes TIS-B tracks (`INCLUDE_TISB` must also be `True`).

Additional configuration parameters, including TAK Server configuration, are included in the [PyTAK Configuration](https://pytak.readthedocs.io/en/latest/configuration/) documentation.





