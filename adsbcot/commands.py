#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Commands."""

import argparse
import asyncio
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

    cot_host, cot_port = pytak.split_host(opts.cot_host, opts.cot_port)
    transport = None

    try:
        if opts.broadcast:
            threads.append(
                pytak.CoTWorker(
                    msg_queue=msg_queue,
                    cot_host=cot_host,
                    cot_port=cot_port,
                    broadcast=opts.broadcast
                )
            )

        [thr.start() for thr in threads]  # NOQA pylint: disable=expression-not-assigned
        msg_queue.join()

        if not opts.broadcast:
            transport, protocol = await loop.create_connection(
                lambda: pytak.AsyncNetworkClient(msg_queue, on_con_lost),
                cot_host, cot_port)

            async def _work_queue():
                #self._logger.debug('Working Queue')
                while not on_con_lost.done():
                    try:
                        msg = await loop.run_in_executor(
                            None,
                            msg_queue.get,
                            (True, 1)
                        )
                        if not msg:
                            continue
                        #self._logger.debug('From msg_queue: "%s"', msg)
                        transport.write(msg)
                    except queue.Empty:
                        pass

            work_queue = _work_queue()
            await work_queue # loop.run_until_complete(work_queue)
            await on_con_lost
        else:
            while all([thr.is_alive() for thr in threads]):
                print(on_con_lost)
                time.sleep(0.01)
    except KeyboardInterrupt:
        [thr.stop() for thr in
         threads]  # NOQA pylint: disable=expression-not-assigned
    finally:
        [thr.stop() for thr in
         threads]  # NOQA pylint: disable=expression-not-assigned
        if not opts.broadcast and transport:
            transport.close()


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

    asyncio.run(main(opts))


if __name__ == '__main__':
    cli()
