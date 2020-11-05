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

ADS-B data can be read from various sources, including:

1. dump1090 Aircraft JSON HTTP feed, see: https://github.com/flightaware/dump1090/blob/master/README-json.md
2. dump1090 Raw & Beast TCP.
3. ADSBExchange API call: https://www.adsbexchange.com/data/
4. [COMING SOON] StratuX WebSockets.
5. [COMING SOON] GDL90

CoT PLIs can be transmitted to SA clients using:

A. TCP Unicast to a specified host:port.
B. [COMING SOON] UDP Broadcast to a specified broadcast host:port or multicast host:port.

For more information on the TAK suite of tools, see: https://www.civtak.org/

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

     usage: adsbcot [-h] -C COT_HOST [-P COT_PORT] [-S STALE] [-I INTERVAL]
                   [-U URL] [-X ADSBX_API_KEY]

      optional arguments:
        -h, --help            show this help message and exit
        -C COT_HOST, --cot_host COT_HOST
                              CoT Destination Host (or Host:Port)
        -P COT_PORT, --cot_port COT_PORT
                              CoT Destination Port
        -S STALE, --stale STALE
                              CoT Stale period, in seconds
        -I INTERVAL, --interval INTERVAL
                              For HTTP: Polling Interval
        -U URL, --url URL     ADS-B Source URL.
        -X ADSBX_API_KEY, --adsbx_api_key ADSBX_API_KEY
                              ADS-B Exchange API Key

At a minimum, you'll need to specify:

1. -C COT_HOST, where COT_HOST is the IP or Hostname of the CoT Event destination.
2. One (1) of the following sets of arguments:
    A. -U DUMP1090_URL, where DUMP1090_URL is the URL to a system running the dump1090 ADS-B decoder.
    B. -U ADSBX_URL & -X ADSBX_API_KEY, where ADSBX_URL is the URL to a ADS-B Exchange feed you'd like to use, and ADSBX_API_KEY is your ADS-B Exchange API Key.

Troubleshooting
===============

To report bugs, please set the DEBUG=1 environment variable to collect logs.

Build Status
============

Master:

.. image:: https://travis-ci.com/ampledata/adsbcot.svg?branch=master
    :target: https://travis-ci.com/ampledata/adsbcot

Develop:

.. image:: https://travis-ci.com/ampledata/adsbcot.svg?branch=develop
    :target: https://travis-ci.com/ampledata/adsbcot

Source
======
Github: https://github.com/ampledata/adsbcot

Author
======
Greg Albrecht W2GMD oss@undef.net

https://ampledata.org/

Copyright
=========
Copyright 2020 Orion Labs, Inc.

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

    $ adsbcot -C 172.17.2.152:8087 -U tcp+beast:172.17.2.122:30005


Connect to dump1090's Raw TCP running on host 172.17.2.122, port 30003 &
forward CoT to host 172.17.2.152, port 8087::

    $ adsbcot -C 172.17.2.152:8087 -U tcp+raw:172.17.2.122:30003


Poll dump1090's JSON API at http://172.17.2.122:8080/data/aircraft.json with a
10 second interval & forward CoT to host 172.17.2.152, port 8087::

    $ adsbcot -C 172.17.2.152:8087 -U http://172.17.2.122:8080/data/aircraft.json -I 10

Poll ADS-B Exchange's API every 5 seconds & forward CoT to host 127.0.0.1, port
8087::

    $ adsbcot -U https://adsbexchange.com/api/aircraft/v2/lat/36.7783/lon/-119.4179/dist/400/ -X SECRET_API_KEY -I 5 -C 127.0.0.1 -P 8087


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
