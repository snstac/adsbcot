ADS-B to Cursor-On-Target Gateway.
**********************************

.. image:: https://raw.githubusercontent.com/ampledata/adsbxcot/main/docs/Screenshot_20201026-142037_ATAK-25p.jpg
   :alt: Screenshot of ADS-B in ATAK.
   :target: https://github.com/ampledata/adsbxcot/blob/main/docs/Screenshot_20201026-142037_ATAK.jpg

The ADS-B to Cursor-On-Target Gateway (ADSBCOT) transforms Automatic Dependent
Surveillance-Broadcast aircraft position information into Cursor On Target 
Position Location Information for display on Situational Awareness 
applications such as the Android Team Awareness Kit (ATAK), WinTAK, RaptorX, 
TAKX, iTAK, et al. For more information on TAK products, see: https://www.tak.gov/

ADS-B data can be recevied from dump1090 using the following network formats:

1. Aircraft JSON HTTP feed. See `dump1090 README-json.md <https://github.com/flightaware/dump1090/blob/master/README-json.md>`_.
2. Raw TCP (via `pyModeS <https://github.com/junzis/pyModeS>`_)
3. Beast TCP (via `pyModeS <https://github.com/junzis/pyModeS>`_)

.. image:: https://raw.githubusercontent.com/ampledata/adsbcot/main/docs/adsbcot_operation.png
   :alt: ADSBCOT Operation Diagram.
   :target: https://github.com/ampledata/adsbcot/blob/main/docs/adsbcot_operation.png

If you'd like to feed ADS-B from another source, consider these tools:

* `adsbxcot <https://github.com/ampledata/adsbxcot>`_: ADSBExchange.com to COT Gateway. Transforms ADS-B position messages to CoT PLI Events.
* `stratuxcot <https://github.com/ampledata/stratuxcot>`_: Stratux ADS-B to COT Gateway. Transforms position messages to CoT PLI Events.


Support Development
===================

**Tech Support**: Email support@undef.net or Signal/WhatsApp: +1-310-621-9598

This tool has been developed for the Disaster Response, Public Safety and
Frontline Healthcare community. This software is currently provided at no-cost
to users. Any contribution you can make to further this project's development
efforts is greatly appreciated.

.. image:: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
    :target: https://www.buymeacoffee.com/ampledata
    :alt: Support Development: Buy me a coffee!


Installation
============

Functionality is provided by a command-line tool called `adsbcot`, which can 
be installed either from the Python Package Index, or directly from this 
source tree.

**To install with HTTP support ONLY:**

Install adsbcot from the Python Package Index (PyPI)::

    $ python3 -m pip install adsbcot

**To install with TCP Beast & TCP Raw support:**

You must install `adsbcot` with the extra `pymodes` package::

    $ python3 -m pip install adsbcot[with_pymodes]

**Alternate / Developers** 

Install adsbcot from the source repository::

    $ git clone https://github.com/ampledata/adsbcot.git
    $ cd adsbcot/
    $ python3 setup.py install


Usage
=====

The `adsbcot` command-line program has 2 runtime arguments::

    usage: adsbcot [-h] [-c CONFIG_FILE]

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG_FILE, --CONFIG_FILE CONFIG_FILE
                            Optional configuration file. Default: config.ini

Configuration Parameters
------------------------
Configuration parameters can be specified either via environment variables or in
a INI-stile configuration file.

Parameters:

* **DUMP1090_URL**: (*optional*) dump1090 source URL, one of: tcp+beast://, tcp+raw:// or http://. Default: tcp+beast://piaware.local:30005 
* **COT_URL**: (*optional*) Destination for Cursor-On-Target messages. See `PyTAK <https://github.com/ampledata/pytak#configuration-parameters>`_ for options.
* **POLL_INTERVAL**: (*optional*) Period in seconds to poll a dump1090 HTTP aircraft.json feed.

There are other configuration parameters available via `PyTAK <https://github.com/ampledata/pytak#configuration-parameters>`_.

Configuration parameters are imported in the following priority order:

1. config.ini (if exists) or -c <filename> (if specified).
2. Environment Variables (if set).
3. Defaults.


Example Configurations
======================

**Example 1**: Connect to dump1090's Beast TCP running on host 172.17.2.122, 
port 30005 & forward COT to host 172.17.2.152, port 8087 use following config.ini::

    [adsbcot]
    COT_URL = tcp://172.17.2.152:8087
    DUMP1090_URL = tcp+beast://172.17.2.122:30005

.. image:: https://raw.githubusercontent.com/ampledata/adsbcot/main/docs/adsbcot_example.png
   :alt: ADSBCOT Example Setup.
   :target: https://github.com/ampledata/adsbcot/blob/main/docs/adsbcot_example.png

**Example 2**: Connect to dump1090's Raw TCP running on host 172.17.2.122, 
port 30002 & forward COT to UDP Multicast Group 239.2.3.1 port 6969::

    [adsbcot]
    COT_URL = udp://239.2.3.1:6969
    DUMP1090_URL = tcp+raw://172.17.2.122:30002

**Example 3**: Poll dump1090's JSON API at 
http://172.17.2.122:8080/data/aircraft.json with a 10 second interval & 
forward COT to host 172.17.2.152, port 8089 using TLS::

    [adsbcot]
    PYTAK_TLS_CLIENT_CERT = /etc/my_client_cert.pem
    COT_URL = tls://tak.example.com:8088
    DUMP1090_URL = http://172.17.2.122:8080/data/aircraft.json
    POLL_INTERVAL = 10

**Example 4**: Use environment variables to set configuration parameters::

    $ export COT_URL="udp://10.9.8.7:8087"
    $ export DUMP1090_URL="tcp+raw://127.0.0.1:30002"
    $ adsbcot


Troubleshooting
===============

To report bugs, please set the DEBUG=1 environment variable to collect logs::

    $ DEBUG=1 adsbcot
    $ # -OR-
    $ export DEBUG=1
    $ adsbcot


Source
======
The source for adsbcot can be found on Github: https://github.com/ampledata/adsbcot


Author
======
adsbcot is written and maintained by Greg Albrecht W2GMD oss@undef.net

https://ampledata.org/


Copyright
=========

* adsbcot is Copyright 2022 Greg Albrecht
* `pyModeS <https://github.com/junzis/pyModeS>`_ is an optional extra package, and is Copyright (C) 2015 Junzi Sun (TU Delft).


License
=======

Copyright 2022 Greg Albrecht <oss@undef.net>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

* `pyModeS <https://github.com/junzis/pyModeS>`_ is an optional extra package, and is licensed under the GNU General Public License v3.0.
