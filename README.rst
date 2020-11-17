adsbcot - ADSB Cursor-on-Target Gateway.
****************************************

.. image:: https://raw.githubusercontent.com/ampledata/adsbcot/main/docs/screenshot-1604561447-25.png
   :alt: Screenshot of ADS-B PLI in ATAK.
   :target: https://github.com/ampledata/adsbcot/blob/main/docs/screenshot-1604561447.png

The adsbcot ADS-B Cursor on Target Gateway transforms Automatic Dependent
Surveillance-Broadcast (ADS-B) aircraft position information into Cursor on
Target (CoT) Position Location Information (PLI) for display on Situational
Awareness (SA) applications such as the Android Team Awareness Kit (ATAK),
WinTAK, RaptorX, et al.

**IF YOU HAVE AN URGENT OPERATIONAL NEED**: Email ops@undef.net or call/sms +1-415-598-8226

ADS-B Data can be recevied from a dump1090 recevier using:
1. Aircraft JSON HTTP feed. See: https://github.com/flightaware/dump1090/blob/master/README-json.md
2. Raw TCP (via `pyModeS <https://github.com/junzis/pyModeS>`_)
3. Beast TCP (via `pyModeS <https://github.com/junzis/pyModeS>`_)

If you'd like to feed AIS data from another source, consider these:

* `adsbxcot <https://github.com/ampledata/adsbxcot>`_: ADS-B Exchange to Cursor on Target (CoT) Gateway. Transforms ADS-B position messages to CoT PLI Events.
* `stratuxcot <https://github.com/ampledata/stratuxcot>`_: Stratux ADS-B to Cursor on Target (CoT) Gateway. Transforms position messages to CoT PLI Events.

Installation
============

The ADS-B to Cursor on Target Gateway is provided by a command-line tool called
`adsbcot`, which can be installed either from the Python Package Index, or
directly from this source tree.

Install from the Python Package Index (PyPI)::

    $ pip install adsbcot


To support direct network streaming (raw & beast) from dump1090, you must
install the extra package `pyModeS <https://github.com/junzis/pyModeS>`_.

To install with pyModeS support::

    $ pip install adsbcot[with_pymodes]


Install from this source tree::

    $ git clone https://github.com/ampledata/adsbcot.git
    $ cd adsbcot/
    $ python setup.py install


Usage
=====

The `adsbcot` command-line program has several runtime arguments::

    usage: adsbcot [-h] -U COT_URL [-S COT_STALE] [-K FTS_TOKEN] -D DUMP1090_URL
                   [-I POLL_INTERVAL]

    optional arguments:
      -h, --help            show this help message and exit
      -U COT_URL, --cot_url COT_URL
                            URL to CoT Destination.
      -S COT_STALE, --cot_stale COT_STALE
                            CoT Stale period, in seconds
      -K FTS_TOKEN, --fts_token FTS_TOKEN
                            FTS REST API Token
      -D DUMP1090_URL, --dump1090_url DUMP1090_URL
                            URL to dump1090 JSON API.
      -I POLL_INTERVAL, --poll_interval POLL_INTERVAL
                            For HTTP: Polling Interval

Troubleshooting
===============

To report bugs, please set the DEBUG=1 environment variable to collect logs.

Unit Test/Build Status
======================

adsbcot's current unit test and build status is available via Travis CI:

.. image:: https://travis-ci.com/ampledata/adsbcot.svg?branch=main
    :target: https://travis-ci.com/ampledata/adsbcot

Source
======
The source for adsbcot can be found on Github: https://github.com/ampledata/adsbcot

Author
======
adsbcot is written and maintained by Greg Albrecht W2GMD oss@undef.net

https://ampledata.org/

Copyright
=========
adsbcot is Copyright 2020 Orion Labs, Inc. https://www.orionlabs.io

`pyModeS <https://github.com/junzis/pyModeS>`_ is an optional extra package,
and is Copyright (C) 2015 Junzi Sun (TU Delft).

License
=======
adsbcot is licensed under the Apache License, Version 2.0. See LICENSE for details.

`pyModeS <https://github.com/junzis/pyModeS>`_ is an optional extra package,
and is licensed under the GNU General Public License v3.0.

Examples
========
Connect to dump1090's Beast TCP running on host 172.17.2.122, port 30005 &
forward CoT to host 172.17.2.152, port 8087::

    $ adsbcot -U 172.17.2.152:8087 -D tcp+beast:172.17.2.122:30005


Connect to dump1090's Raw TCP running on host 172.17.2.122, port 30002 &
forward CoT to host 172.17.2.152, port 8087::

    $ adsbcot -U 172.17.2.152:8087 -D tcp+raw:172.17.2.122:30002


Poll dump1090's JSON API at http://172.17.2.122:8080/data/aircraft.json with a
10 second interval & forward CoT to host 172.17.2.152, port 8087::

    $ adsbcot -U 172.17.2.152:8087 -D http://172.17.2.122:8080/data/aircraft.json -I 10

Running as a Daemon
===================
First, install supervisor::

    $ sudo yum install supervisor
    $ sudo service supervisord start

Create /etc/supervisor.d/adsbcot.ini with the following content::

    [program:adsbcot]
    command=adsbcot -U https://adsbexchange.com/api/aircraft/v2/lat/36.7783/lon/-119.4179/dist/400/ -X xxx -I 5 -C 127.0.0.1 -P 8087

And update supervisor::

    $ sudo supervisorctl update
