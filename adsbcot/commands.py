#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Commands."""

import argparse
import queue
import time

import adsbcot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


def cli():
    """Command Line interface for ADS-B Cursor-on-Target Gateway."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-C', '--cot_host', help='CoT Destination Host (or Host:Port)',
        required=True
    )
    parser.add_argument(
        '-P', '--cot_port', help='CoT Destination Port'
    )
    parser.add_argument(
        '-B', '--broadcast', help='UDP Broadcast CoT?',
        action='store_true'
    )
    parser.add_argument(
        '-I', '--interval', help='URL Polling Interval',
    )
    parser.add_argument(
        '-S', '--stale', help='CoT Stale period, in hours',
    )
    parser.add_argument(
        '-D', '--dump1090_url', help='Dump1090 URL'
    )
    parser.add_argument(
        '-U', '--adsbx_url', help='ADS-B Exchange API URL',
    )
    parser.add_argument(
        '-X', '--adsbx_api_key', help='ADS-B Exchange API Key',
    )
    opts = parser.parse_args()

    threads: list = []
    msg_queue: queue.Queue = queue.Queue()

    adsbworker = adsbcot.ADSBWorker(
        msg_queue=msg_queue,
        url=opts.dump1090_url or opts.adsbx_url,
        interval=opts.interval,
        stale=opts.stale,
        api_key=opts.adsbx_api_key
    )
    threads.append(adsbworker)

    cotworker = adsbcot.CoTWorker(
        msg_queue=msg_queue,
        cot_host=opts.cot_host,
        cot_port=opts.cot_port,
        broadcast=opts.broadcast
    )
    threads.append(cotworker)

    try:
        [thr.start() for thr in threads]  # NOQA pylint: disable=expression-not-assigned
        msg_queue.join()

        while all([thr.is_alive() for thr in threads]):
            time.sleep(0.01)
    except KeyboardInterrupt:
        [thr.stop() for thr in
         threads]  # NOQA pylint: disable=expression-not-assigned
    finally:
        [thr.stop() for thr in
         threads]  # NOQA pylint: disable=expression-not-assigned


if __name__ == '__main__':
    cli()
