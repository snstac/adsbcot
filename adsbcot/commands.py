#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Commands."""

import aiohttp
import argparse
import asyncio
import concurrent
import os
import sys
import urllib

import pytak

import adsbcot

with_pymodes = False
try:
    import pyModeS
    with_pymodes = True
except ImportError:
    pass

# Python 3.6 support:
if sys.version_info[:2] >= (3, 7):
    from asyncio import get_running_loop
else:
    from asyncio import _get_running_loop as get_running_loop

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'



async def main(opts):
    loop = asyncio.get_running_loop()
    tx_queue: asyncio.Queue = asyncio.Queue()
    rx_queue: asyncio.Queue = asyncio.Queue()
    cot_url: urllib.parse.ParseResult = urllib.parse.urlparse(opts.cot_url)

    # Create our CoT Event Queue Worker
    reader, writer = await pytak.protocol_factory(cot_url)
    write_worker = pytak.EventTransmitter(tx_queue, writer)
    read_worker = pytak.EventReceiver(rx_queue, reader)

    tasks = set()
    dump1090_url: urllib.parse.ParseResult = urllib.parse.urlparse(
        opts.dump1090_url)

    # ADSB Workers (receivers):
    if "http" in dump1090_url.scheme:
        message_worker = adsbcot.ADSBWorker(
            event_queue=tx_queue,
            url=dump1090_url,
            poll_interval=opts.poll_interval,
            cot_stale=opts.cot_stale
        )
    elif "tcp" in dump1090_url.scheme:
        if not with_pymodes:
            print('ERROR from adsbcot')
            print('Please reinstall adsbcot with pyModeS support: ')
            print('$ pip install -U adsbcot[with_pymodes]')
            print('Exiting...')
            raise Exception

        net_queue: asyncio.Queue = asyncio.Queue(loop=loop)

        if "+" in dump1090_url.scheme:
            _, data_type = dump1090_url.scheme.split("+")
        else:
            data_type = "raw"

        adsbnetreceiver = adsbcot.ADSBNetReceiver(
            net_queue, dump1090_url, data_type)

        tasks.add(asyncio.ensure_future(adsbnetreceiver.run()))

        message_worker = adsbcot.ADSBNetWorker(
            event_queue=tx_queue,
            net_queue=net_queue,
            data_type=data_type,
            cot_stale=opts.cot_stale
        )

    await tx_queue.put(adsbcot.hello_event())

    tasks.add(asyncio.ensure_future(message_worker.run()))
    tasks.add(asyncio.ensure_future(read_worker.run()))
    tasks.add(asyncio.ensure_future(write_worker.run()))

    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in done:
        print(f"Task completed: {task}")



def cli():
    """Command Line interface for ADS-B Cursor-on-Target Gateway."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-U', '--cot_url', help='URL to CoT Destination.',
        required=True
    )
    parser.add_argument(
        '-S', '--cot_stale', help='CoT Stale period, in seconds',
        default=adsbcot.DEFAULT_COT_STALE
    )
    parser.add_argument(
        '-K', '--fts_token', help='FTS REST API Token'
    )
    parser.add_argument(
        '-D', '--dump1090_url', help='URL to dump1090 JSON API.',
        required=True
    )
    parser.add_argument(
        '-I', '--poll_interval', help='For HTTP: Polling Interval',
    )
    opts = parser.parse_args()

    if sys.version_info[:2] >= (3, 7):
        asyncio.run(main(opts), debug=bool(os.environ.get('DEBUG')))
    else:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main(opts))
        finally:
            loop.close()


if __name__ == '__main__':
    cli()
