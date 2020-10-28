#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Commands."""

import argparse
import asyncio
import concurrent
import os
import queue
import time

import pytak

import adsbcot

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


async def main(opts):
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()

    msg_queue: asyncio.Queue = asyncio.Queue(loop=loop)

    adsbworker = adsbcot.ADSBWorker(
        msg_queue=msg_queue,
        url=opts.dump1090_url or opts.adsbx_url,
        interval=opts.interval,
        stale=opts.stale,
        api_key=opts.adsbx_api_key
    )

    cot_host, cot_port = pytak.split_host(opts.cot_host, opts.cot_port)

    client_factory = pytak.AsyncNetworkClient(msg_queue, on_con_lost)
    transport, protocol = await loop.create_connection(
        lambda: client_factory, cot_host, cot_port)

    cotworker = pytak.AsyncCoTWorker(msg_queue, transport)

    tasks: set = set()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    tasks.add(asyncio.ensure_future(cotworker.run()))
    tasks.add(asyncio.ensure_future(adsbworker.run()))
    tasks.add(await on_con_lost)
    tasks.add(asyncio.ensure_future(msg_queue.join()))

    done, pending = loop.run_until_complete(
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED))

    for task in done:
        self._logger.debug('Task completed: %s', task)


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

    asyncio.run(main(opts), debug=bool(os.environ.get('DEBUG')))


if __name__ == '__main__':
    cli()
