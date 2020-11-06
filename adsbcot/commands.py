#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Commands."""

import aiohttp
import argparse
import asyncio
import concurrent
import os
import urllib

import pytak

import adsbcot

with_pymodes = False
try:
    import pyModeS
    with_pymodes = True
except ImportError:
    pass

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


async def main(opts):
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()
    tasks: set = set()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
    msg_queue: asyncio.Queue = asyncio.Queue(loop=loop)
    transport = None
    send_obj = False
    net_queue = None
    url: urllib.parse.ParseResult = urllib.parse.urlparse(opts.url)

    # CoT/TAK Workers (transmitters):
    if opts.fts_url:
        fts_url: urllib.parse.ParseResult = urllib.parse.urlparse(opts.fts_url)
        if 'http' in fts_url.scheme:
            cotworker = pytak.FTSClient(
                msg_queue, fts_url.geturl(), opts.fts_token)
            send_obj = True
    else:
        cot_host, cot_port = pytak.split_host(opts.cot_host, opts.cot_port)
        client_factory = pytak.AsyncNetworkClient(msg_queue, on_con_lost)
        transport, protocol = await loop.create_connection(
            lambda: client_factory, cot_host, cot_port)
        cotworker = pytak.AsyncCoTWorker(msg_queue, transport)

    # ADSB Workers (receivers):
    if 'http' in url.scheme:
        adsbworker = adsbcot.ADSBWorker(
            msg_queue=msg_queue,
            url=url,
            interval=opts.interval,
            stale=opts.stale,
            api_key=opts.adsbx_api_key,
            send_obj=send_obj
        )
        tasks.add(asyncio.ensure_future(adsbworker.run()))
    elif 'tcp' in url.scheme:
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
            stale=opts.stale,
            send_obj=send_obj
        )
        tasks.add(asyncio.ensure_future(adsbnetworker.run()))

    tasks.add(asyncio.ensure_future(cotworker.run()))
    if transport:
        tasks.add(await on_con_lost)
    #if net_queue:
    #    tasks.add(asyncio.ensure_future(net_queue.join()))
    #tasks.add(asyncio.ensure_future(msg_queue.join()))

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in done:
        print(f"Task completed: {task}")


def cli():
    """Command Line interface for ADS-B Cursor-on-Target Gateway."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-C', '--cot_host', help='CoT Destination Host (or Host:Port, or URL)'
    )
    parser.add_argument(
        '-P', '--cot_port', help='CoT Destination Port'
    )
    #parser.add_argument(
    #    '-B', '--broadcast', help='UDP Broadcast CoT?',
    #    action='store_true'
    #)
    parser.add_argument(
        '-S', '--stale', help='CoT Stale period, in seconds',
    )

    parser.add_argument(
        '-I', '--interval', help='For HTTP: Polling Interval',
    )

    parser.add_argument(
        '-U', '--url', help='ADS-B Source URL.',
    )

    parser.add_argument(
        '-X', '--adsbx_api_key', help='ADS-B Exchange API Key',
    )

    parser.add_argument(
        '-F', '--fts_url', help='FTS REST API URL'
    )
    parser.add_argument(
        '-K', '--fts_token', help='FTS REST API Token'
    )
    opts = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(opts)) #, debug=bool(os.environ.get('DEBUG')))
    finally:
        loop.close()

    # asyncio.run(main(opts), debug=bool(os.environ.get('DEBUG')))


if __name__ == '__main__':
    cli()
