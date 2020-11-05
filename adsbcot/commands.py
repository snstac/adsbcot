#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Commands."""

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

    msg_queue: asyncio.Queue = asyncio.Queue(loop=loop)

    cot_host, cot_port = pytak.split_host(opts.cot_host, opts.cot_port)
    url: urllib.parse.ParseResult = urllib.parse.urlparse(opts.url)

    client_factory = pytak.AsyncNetworkClient(msg_queue, on_con_lost)
    transport, protocol = await loop.create_connection(
        lambda: client_factory, cot_host, cot_port)

    cotworker = pytak.AsyncCoTWorker(msg_queue, transport)

    tasks: set = set()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)

    if 'http' in url.scheme:
        adsbworker = adsbcot.ADSBWorker(
            msg_queue=msg_queue,
            url=url,
            interval=opts.interval,
            stale=opts.stale,
            api_key=opts.adsbx_api_key
        )
        tasks.add(asyncio.ensure_future(adsbworker.run()))
    elif 'tcp' in url.scheme:
        if not with_pymodes:
            print('ERROR from adsbcot')
            print('Please reinstall adsbcot with pyModeS support: ')
            print('$ pip install -U adsbcot[with_pymodes]')
            print('Exiting...')
            return False

        net_queue: asyncio.Queue = asyncio.Queue(loop=loop)
        tasks.add(asyncio.ensure_future(net_queue.join()))

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
            stale=opts.stale
        )
        tasks.add(asyncio.ensure_future(adsbnetworker.run()))

    tasks.add(asyncio.ensure_future(cotworker.run()))
    tasks.add(await on_con_lost)
    tasks.add(asyncio.ensure_future(msg_queue.join()))

    done, pending = loop.run_until_complete(
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED))

    for task in done:
        print(f"Task completed: {task}")


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
    opts = parser.parse_args()

    asyncio.run(main(opts), debug=bool(os.environ.get('DEBUG')))


if __name__ == '__main__':
    cli()
