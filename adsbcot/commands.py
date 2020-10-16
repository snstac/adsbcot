#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Commands."""

import argparse
import time

import adsbcot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


def cli():
    """Command Line interface for ADS-B Cursor-on-Target Gateway."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-D', '--dump1090_url', help='Dump1090 URL'
    )
    parser.add_argument(
        '-C', '--cot_host', help='Cursor-on-Target Host or Host:Port',
        required=True
    )
    opts = parser.parse_args()

    adsbcot_i = adsbcot.ADSBCoT(opts.dump1090_url, opts.cot_host)

    try:
        adsbcot_i.start()

        while adsbcot_i.is_alive():
            time.sleep(0.01)
    except KeyboardInterrupt:
        adsbcot_i.stop()
    finally:
        adsbcot_i.stop()


if __name__ == '__main__':
    cli()
