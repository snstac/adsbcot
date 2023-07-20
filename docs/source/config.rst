Configuration
=============

ADSBCOT's configuration parameters can be set two ways:

1. In an INI-style configuration file, typically ``adsbcot.ini``
2. As environment variables.

ADSBCOT has the following built-in configuration parameters:

.. describe:: COT_URL (optional)

  Destination for Cursor on Target messages. Defaults to ``udp+wo://239.2.3.1:6969`` (ATAK 'Mesh SA' default, multicast)

.. describe:: FEED_URL (optional)

  Source of dump1090 decoded ADS-B data. Should start with one of: ``tcp://``, ``tcp+beast://``, ``tcp+raw://``, ``http://``, or ``file://``. Defaults to ``file:///run/dump1090-fa/aircraft.json`` (dump1090-fa's local JSON file).

.. describe:: POLL_INTERVAL (optional)

  Period, in seconds, to poll the FEED_URL, if the FEED_URL is of the type HTTP.

.. describe:: ALT_UPPER (optional)

  Upper Altitude Limit, geometric (GNSS / INS) altitude in feet referenced to the WGS84 ellipsoid.

.. describe:: ALT_LOWER: (optional)

  Lower Altitude Limit, geometric (GNSS / INS) altitude in feet referenced to the WGS84 ellipsoid.

There are other configuration parameters, including TLS support, are described in the `PyTAK <https://pytak.readthedocs.io/en/latest/config.html>`_ documentation.

Configuration parameters are imported in the following priority order:

1. config.ini (if exists) or -c <filename> (if specified).
2. Environment Variables (if set).
3. Defaults.


Example Configurations
----------------------

**Example 1**: Connect to dump1090's Beast TCP running on host 172.17.2.122, 
port 30003 & forward COT to host 172.17.2.152, port 8087 use following config.ini::

    [adsbcot]
    COT_URL = tcp://172.17.2.152:8087
    FEED_URL = tcp+beast://172.17.2.122:30003

.. image:: https://raw.githubusercontent.com/snstac/adsbcot/main/docs/adsbcot_example.png
   :alt: ADSBCOT Example Setup.
   :target: https://github.com/snstac/adsbcot/blob/main/docs/adsbcot_example.png

**Example 2**: Connect to dump1090's Raw TCP running on host 172.17.2.122, 
port 30005 & forward COT to UDP Multicast Group 239.2.3.1 port 6969::

    [adsbcot]
    COT_URL = udp://239.2.3.1:6969
    FEED_URL = tcp+raw://172.17.2.122:30005

**Example 3**: Poll dump1090's JSON API at 
http://172.17.2.122:8080/data/aircraft.json with a 10 second interval & 
forward COT to host 172.17.2.152, port 8089 using TLS::

    [adsbcot]
    PYTAK_TLS_CLIENT_CERT = /etc/my_client_cert.pem
    COT_URL = tls://tak.example.com:8088
    FEED_URL = http://172.17.2.122:8080/data/aircraft.json
    POLL_INTERVAL = 10

**Example 4**: Use environment variables to set configuration parameters::

    $ export COT_URL="udp://10.9.8.7:8087"
    $ export FEED_URL="tcp+raw://127.0.0.1:30002"
    $ adsbcot

