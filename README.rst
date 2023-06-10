ADS-B to TAK Gateway
********************

.. image:: https://github.com/snstac/adsbcot/blob/main/docs/atak_screenshot_with_pytak_logo-x25.jpg
   :alt: ATAK Screenshot with PyTAK Logo.
   :target: https://github.com/snstac/adsbcot/blob/main/docs/atak_screenshot_with_pytak_logo.jpg

The ADS-B to TAK Gateway (ADSBCOT) transforms Automatic Dependent 
Surveillance-Broadcast (ADS-B) aircraft position information into Cursor on 
Target for display on `TAK Products <https://tak.gov/>`_ such as ATAK, WinTAK & iTAK.

ADS-B data can be recevied from dump1090 using the following network formats:

1. Local file.
2. Aircraft JSON HTTP feed. See `dump1090 README-json.md <https://github.com/flightaware/dump1090/blob/master/README-json.md>`_.
3. Raw TCP (via `pyModeS <https://github.com/junzis/pyModeS>`_)
4. Beast TCP (via `pyModeS <https://github.com/junzis/pyModeS>`_)

.. image:: https://raw.githubusercontent.com/ampledata/adsbcot/main/docs/adsbcot_operation.png
   :alt: ADSBCOT Operation Diagram.
   :target: https://github.com/ampledata/adsbcot/blob/main/docs/adsbcot_operation.png

If you'd like to feed ADS-B from another source, consider these tools:

* `adsbxcot <https://github.com/ampledata/adsbxcot>`_: ADSBExchange.com to CoT Gateway. Transforms ADS-B position messages to CoT PLI Events.
* `stratuxcot <https://github.com/ampledata/stratuxcot>`_: Stratux ADS-B to CoT Gateway. Transforms position messages to CoT PLI Events.

Documentation
=============

See `ADSBCOT documentation <https://adsbcot.readthedocs.io/>`_.


Troubleshooting
===============

To report bugs, please set the DEBUG=1 environment variable to collect logs::

    $ DEBUG=1 adsbcot
    $ # -OR-
    $ export DEBUG=1
    $ adsbcot


License & Copyright
===================

Copyright 2023 Sensors & Signals LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

* `pyModeS <https://github.com/junzis/pyModeS>`_ is an optional extra package, and is licensed under the GNU General Public License v3.0.
