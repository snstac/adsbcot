ADS-B to Cursor-On-Target Gateway.
**********************************

.. image:: https://raw.githubusercontent.com/ampledata/adsbxcot/main/docs/Screenshot_20201026-142037_ATAK-25p.jpg
   :alt: Screenshot of ADS-B PLI in ATAK.
   :target: https://github.com/ampledata/adsbxcot/blob/main/docs/Screenshot_20201026-142037_ATAK.jpg


**IF YOU HAVE AN URGENT OPERATIONAL NEED**: Email ops@undef.net or sms+call +1-415-598-8226

The ADSBCOT ADS-B to Cursor-On-Target Gateway transforms Automatic Dependent
Surveillance-Broadcast (ADS-B) aircraft position information into Cursor On
Target (COT) Position Location Information (PLI) for display on Situational
Awareness (SA) applications such as the Android Team Awareness Kit (ATAK),
WinTAK, RaptorX, TAKX, iTAK, et al.

For more information on the TAK suite of tools, see: https://www.tak.gov/

ADS-B Data can be recevied from a dump1090 recevier using:

1. Aircraft JSON HTTP feed. See: https://github.com/flightaware/dump1090/blob/master/README-json.md
2. Raw TCP (via `pyModeS <https://github.com/junzis/pyModeS>`_)
3. Beast TCP (via `pyModeS <https://github.com/junzis/pyModeS>`_)

If you'd like to feed ADS-B from another source, consider these:

* `adsbxcot <https://github.com/ampledata/adsbxcot>`_: ADS-B Exchange to Cursor on Target (COT) Gateway. Transforms ADS-B position messages to CoT PLI Events.
* `stratuxcot <https://github.com/ampledata/stratuxcot>`_: Stratux ADS-B to Cursor on Target (COT) Gateway. Transforms position messages to CoT PLI Events.

Support ADSBCOT Development
===========================

ADSBCOT has been developed for the Disaster Response, Public Safety and
Frontline Healthcare community. This software is currently provided at no-cost
to users. Any contribution you can make to further this project's development
efforts is greatly appreciated.

.. image:: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
    :target: https://www.buymeacoffee.com/ampledata
    :alt: Support ADSBCOT development: Buy me a coffee!

Installation
============

The ADS-B to Cursor on Target Gateway is provided by a command-line tool called
`adsbcot`, which can be installed either from the Python Package Index, or
directly from this source tree.

Install from the Python Package Index (PyPI)::

    $ python3 -m pip install adsbcot


To support direct network streaming (raw & beast) from dump1090, you must
install the extra package `pyModeS <https://github.com/junzis/pyModeS>`_.

To install with pyModeS support::

    $ python3 -m pip install adsbcot[with_pymodes]


Install from this source tree::

    $ git clone https://github.com/ampledata/adsbcot.git
    $ cd adsbcot/
    $ python3 setup.py install


Usage
=====

The `adsbcot` command-line program has several runtime arguments::

    usage: adsbcot [-h] [-c CONFIG_FILE]

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG_FILE, --CONFIG_FILE CONFIG_FILE
    

Example config.ini
==================
Connect to dump1090's Beast TCP running on host 172.17.2.122, port 30005 &
forward CoT to host 172.17.2.152, port 8087 use following config.ini::

    [adsbcot]
    COT_URL = 172.17.2.152:8087
    DUMP1090_URL = tcp+beast://172.17.2.122:30005

Connect to dump1090's Raw TCP running on host 172.17.2.122, port 30002 &
forward CoT to host 172.17.2.152, port 8087::

    [adsbcot]
    COT_URL = 172.17.2.152:8087
    DUMP1090_URL = tcp+raw://172.17.2.122:30002


Poll dump1090's JSON API at http://172.17.2.122:8080/data/aircraft.json with a
10 second interval & forward CoT to host 172.17.2.152, port 8087::

    [adsbcot]
    COT_URL = 172.17.2.152:8087
    DUMP1090_URL = thttp://172.17.2.122:8080/data/aircraft.json
    POLL_INTERVAL = 10


Troubleshooting
===============

To report bugs, please set the DEBUG=1 environment variable to collect logs::

    $ DEBUG=1 adsbcot -c config.ini

Source
======
The source for adsbcot can be found on Github: https://github.com/ampledata/adsbcot

Author
======
adsbcot is written and maintained by Greg Albrecht W2GMD oss@undef.net

https://ampledata.org/

Copyright
=========
adsbcot is Copyright 2022 Greg Albrecht

`pyModeS <https://github.com/junzis/pyModeS>`_ is an optional extra package,
and is Copyright (C) 2015 Junzi Sun (TU Delft).

License
=======
adsbcot is licensed under the Apache License, Version 2.0. See LICENSE for details.

`pyModeS <https://github.com/junzis/pyModeS>`_ is an optional extra package,
and is licensed under the GNU General Public License v3.0.
