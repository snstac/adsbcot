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
    loop = get_running_loop()

    tasks: set = set()
    event_queue: asyncio.Queue = asyncio.Queue(loop=loop)

    cot_url: urllib.parse.ParseResult = urllib.parse.urlparse(opts.cot_url)
    adsb_url: urllib.parse.ParseResult = urllib.parse.urlparse(opts.adsb_url)

    # CoT/TAK Event Workers (transmitters):
    if "http" in cot_url.scheme:
        eventworker = pytak.FTSClient(
            event_queue, cot_url.geturl(), opts.fts_token)
    elif "tcp" in cot_url.scheme:
        host, port = pytak.parse_cot_url(cot_url)
        _, writer = await asyncio.open_connection(host, port)
        eventworker = pytak.EventWorker(event_queue, writer)
    elif "udp" in cot_url.scheme:
        writer = await pytak.udp_client(cot_url)
        eventworker = pytak.EventWorker(event_queue, writer)

    # ADSB Workers (receivers):
    if "http" in adsb_url.scheme:
        adsbworker = adsbcot.ADSBWorker(
            event_queue=event_queue,
            url=adsb_url,
            poll_interval=opts.poll_interval,
            cot_stale=opts.cot_stale,
            api_key=opts.adsbx_api_key,
        )
    elif "tcp" in adsb_url.scheme:
        if not with_pymodes:
            print('ERROR from adsbcot')
            print('Please reinstall adsbcot with pyModeS support: ')
            print('$ pip install -U adsbcot[with_pymodes]')
            print('Exiting...')
            raise Exception

        net_queue: asyncio.Queue = asyncio.Queue(loop=loop)

        adsbnetreceiver = adsbcot.ADSBNetReceiver(net_queue, url)
        tasks.add(asyncio.ensure_future(adsbnetreceiver.run()))

        if '+' in url.scheme:
            _, data_type = url.scheme.split('+')
        else:
            data_type = 'raw'

        print(f"Using data_type={data_type}")

        adsbnetworker = adsbcot.ADSBNetWorker(
            msg_queue=msg_queue,
            net_queue=net_queue,
            data_type=data_type,
            cot_stale=opts.cot_stale
        )
        tasks.add(asyncio.ensure_future(adsbnetworker.run()))

    tasks.add(asyncio.ensure_future(adsbworker.run()))
    tasks.add(asyncio.ensure_future(eventworker.run()))

    done, pending = await asyncio.wait(
        tasks, return_when=asyncio.FIRST_COMPLETED)

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
        '-A', '--adsb_url', help='URL to ADS-B Source.',
        required=True
    )

    parser.add_argument(
        '-S', '--cot_stale', help='CoT Stale period, in seconds',
    )
    parser.add_argument(
        '-K', '--fts_token', help='FTS REST API Token'
    )

    parser.add_argument(
        '-I', '--poll_interval', help='For HTTP: Polling Interval',
    )
    parser.add_argument(
        '-X', '--adsbx_api_key', help='ADS-B Exchange API Key',
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
