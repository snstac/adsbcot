.. image:: ../atak_screenshot_with_pytak_logo-x25.jpg
   :alt: ATAK Screenshot with PyTAK Logo.

ADS-B to TAK Gateway Documentation
==================================

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

* `adsbxcot <https://github.com/ampledata/adsbxcot>`_: ADSBExchange.com & adsb.fi to TAK Gateway.
* `stratuxcot <https://github.com/ampledata/stratuxcot>`_: Stratux ADS-B to TAK Gateway.



Quickstart
----------

1. do stuff.

2. do other stuff:

   .. code-block:: Python

   pythong stuff

   See :doc:`config` for config examples.

3. do last stuff

Contents
--------
.. toctree::
   :maxdepth: 2

   install
   config
   compat
   clients
   examples
   api

.. seealso::

   `adsbcot source code on Github <https://github.com/snstac/adsbcot>`_

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

(adsbcot |version|)