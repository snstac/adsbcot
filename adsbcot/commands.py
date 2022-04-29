#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Gateway Commands."""

import argparse
import asyncio
import configparser
import collections
import logging
import os
import platform
import sys
import typing

from urllib.parse import ParseResult, urlparse

import pytak

import adsbcot

# We won't use pyModeS if it isn't installed:
WITH_PYMODES = False
try:
    import pyModeS  # pylint: disable=unused-import

    WITH_PYMODES = True
except ImportError:
    pass

# Python 3.6 support:
if sys.version_info[:2] >= (3, 7):
    from asyncio import get_running_loop
else:
    from asyncio import _get_running_loop as get_running_loop

__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


async def main(  # pylint: disable=too-many-locals
    opts: typing.ChainMap[str, typing.Any]
) -> None:  # pylint: disable=too-many-locals
    tx_queue: asyncio.Queue = asyncio.Queue()
    rx_queue: asyncio.Queue = asyncio.Queue()
    cot_url: ParseResult = urlparse(opts.get("COT_URL"))

    # Create our COT Event Queue Worker
    reader, writer = await pytak.protocol_factory(cot_url)
    write_worker = pytak.EventTransmitter(tx_queue, writer)
    read_worker = pytak.EventReceiver(rx_queue, reader)

    dump1090_url: ParseResult = urlparse(opts.get("DUMP1090_URL"))

    tasks = set()

    # ADSB Workers (receivers):
    if "http" in dump1090_url.scheme:
        message_worker = adsbcot.ADSBWorker(
            event_queue=tx_queue,
            url=dump1090_url,
            poll_interval=opts.get("POLL_INTERVAL"),
            cot_stale=opts.get("COT_STALE"),
            filters=opts.get("FILTERS"),
        )
    elif "tcp" in dump1090_url.scheme:
        if not WITH_PYMODES:
            print("ERROR from adsbcot")
            print("Please reinstall adsbcot with pyModeS support: ")
            print("$ python3 -m pip install adsbcot[with_pymodes]")
            print("Exiting...")
            raise Exception

        net_queue: asyncio.Queue = asyncio.Queue()

        if "+" in dump1090_url.scheme:
            _, data_type = dump1090_url.scheme.split("+")
        else:
            data_type = "raw"

        adsbnetreceiver = adsbcot.ADSBNetReceiver(net_queue, dump1090_url, data_type)

        tasks.add(asyncio.ensure_future(adsbnetreceiver.run()))

        message_worker = adsbcot.ADSBNetWorker(
            event_queue=tx_queue,
            net_queue=net_queue,
            data_type=data_type,
            cot_stale=opts.get("COT_STALE"),
            filters=opts.get("FILTERS"),
        )

    await tx_queue.put(pytak.hello_event(f"adsbxcot@{platform.node()}"))

    tasks.add(asyncio.ensure_future(message_worker.run()))
    tasks.add(asyncio.ensure_future(read_worker.run()))
    tasks.add(asyncio.ensure_future(write_worker.run()))

    done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in done:
        print(f"Task completed: {task}")


def cli() -> None:
    """Command Line interface for ADS-B Cursor-on-Target Gateway."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c", "--CONFIG_FILE", dest="CONFIG_FILE", default="config.ini", type=str
    )

    namespace = parser.parse_args()
    cli_args = {k: v for k, v in vars(namespace).items() if v is not None}

    # Read config file:
    config_file = cli_args.get("CONFIG_FILE")
    logging.info("Reading configuration from %s", config_file)
    config = configparser.ConfigParser()
    config.read(config_file)

    # Combined command-line args with config file:
    combined_config = collections.ChainMap(cli_args, os.environ, config["adsbcot"])

    if combined_config.get("FILTER_CONFIG"):
        filter_config = combined_config.get("FILTER_CONFIG")
        logging.info("Reading FILTER_CONFIG from %s", filter_config)
        filters = configparser.ConfigParser()
        filters.read(filter_config)
        combined_config = collections.ChainMap(combined_config, {"FILTERS": filters})

    if sys.version_info[:2] >= (3, 7):
        asyncio.run(main(combined_config), debug=os.getenv("DEBUG"))
    else:
        loop = get_running_loop()
        try:
            loop.run_until_complete(main(combined_config))
        finally:
            loop.close()


if __name__ == "__main__":
    cli()
