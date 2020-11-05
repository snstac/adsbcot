#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Class Definitions."""

#import aiofiles
import concurrent

import aiohttp
import asyncio
import json
import logging
import os
import queue
import random
import threading
import time
import urllib

import pycot
import requests

import adsbcot

with_pymodes = False
try:
    import pyModeS.streamer.source
    import pyModeS.streamer.decode
    import pyModeS as pms
    with_pymodes = True
except ImportError:
    pass


__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


class ADSBWorker:

    """Reads ADS-B Data from inputs, renders to CoT, and puts on queue."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(adsbcot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(adsbcot.LOG_LEVEL)
        _console_handler.setFormatter(adsbcot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger('asyncio').setLevel(adsbcot.LOG_LEVEL)

    def __init__(self, msg_queue: asyncio.Queue, url: urllib.parse.ParseResult,
                 interval: int = None, stale: int = None, api_key: str = None):
        self.msg_queue = msg_queue
        self.url: urllib.parse.ParseResult = url
        self.interval: int = int(interval or adsbcot.DEFAULT_INTERVAL)
        self.stale: int = stale
        self.api_key: str = api_key

    async def _put_msg_queue(self, aircraft: list) -> None:
        if not aircraft:
            self._logger.warning('Empty aircraft list')
            return False

        i = 1
        for craft in aircraft:
            cot_event = adsbcot.adsb_to_cot(craft, stale=self.stale)
            if not cot_event:
                self._logger.debug(f'Empty CoT Event for craft={craft}')
                i += 1
                continue

            self._logger.debug(
                'Handling %s/%s ICAO24: %s Flight: %s ',
                i, len(aircraft), craft.get('hex'), craft.get('flight'))

            rendered_event = cot_event.render(
                encoding='UTF-8', standalone=True)

            if rendered_event:
                try:
                    await self.msg_queue.put(rendered_event)
                except queue.Full as exc:
                    self._logger.exception(exc)
                    self._logger.warning(
                        'Lost CoT Event (queue full): "%s"', rendered_event)
            i += 1

    async def _get_dump1090_feed(self):
        async with aiohttp.ClientSession() as session:
            resp = await session.request(method='GET', url=self.url.geturl())
            resp.raise_for_status()
            json_resp = await resp.json()
            aircraft = json_resp.get('aircraft')
            self._logger.debug('Retrieved %s aircraft', len(aircraft))
            await self._put_msg_queue(aircraft)

    async def _get_adsbx_feed(self) -> None:
        headers = {'api-auth': self.api_key}
        response = requests.get(self.url.geturl(), headers=headers)
        jresponse = json.loads(response.text)
        aircraft = jresponse.get('ac')
        self._logger.debug('Retrieved %s aircraft', len(aircraft))
        await self._put_msg_queue(aircraft)

    async def run(self):
        """Runs this Thread, Reads from Pollers."""
        self._logger.info("Running ADSBWorker with URL '%s'", self.url.geturl())

        await self.msg_queue.put(
            adsbcot.hello_event().render(encoding='UTF-8', standalone=True))

        if 'aircraft.json' in self.url.path:
            feed_func = self._get_dump1090_feed
        else:
            feed_func = self._get_adsbx_feed

        self._logger.debug("url=%s feed_func=%s", self.url, feed_func)
        while 1:
            await feed_func()
            await asyncio.sleep(self.interval)


class ADSBNetReceiver:

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(adsbcot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(adsbcot.LOG_LEVEL)
        _console_handler.setFormatter(adsbcot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger('asyncio').setLevel(adsbcot.LOG_LEVEL)

    def __init__(self, net_queue, url):
        self.net_queue = net_queue
        self.url = url

    async def run(self):
        self._logger.info(
            "Running ADSBNetReceiver for URL=%s", self.url.geturl())

        if ":" in self.url.path:
            host, port = self.url.path.split(":")
        else:
            host = self.url.path
            port = adsbcot.DEFAULT_DUMP1090_TCP_PORT

        self._logger.debug("host=%s port=%s", host, port)
        reader, writer = await asyncio.open_connection(host, port)
        while 1:
            received = await reader.read(4096)
            self.net_queue.put_nowait(received)


class ADSBNetWorker:

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(adsbcot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(adsbcot.LOG_LEVEL)
        _console_handler.setFormatter(adsbcot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger('asyncio').setLevel(adsbcot.LOG_LEVEL)

    def __init__(self, msg_queue, net_queue, data_type, stale):
        self.msg_queue = msg_queue
        self.net_queue = net_queue
        self.data_type = data_type
        self.stale = stale

    async def _put_msg_queue(self, aircraft: list) -> None:
        if not aircraft:
            self._logger.warning('Empty aircraft list')
            return

        i = 1
        for craft in aircraft:

            cot_event = adsbcot.adsb_to_cot(craft, stale=self.stale)
            self._logger.debug("craft: %s", craft)
            if not cot_event:
                self._logger.debug(f'Empty CoT Event for craft={craft}')
                i += 1
                continue

            self._logger.debug(
                'Handling %s/%s ICAO24: %s Flight: %s ',
                i, len(aircraft), craft.get('hex'), craft.get('flight'))

            rendered_event = cot_event.render(
                encoding='UTF-8', standalone=True)

            if rendered_event:
                try:
                    await self.msg_queue.put(rendered_event)
                except queue.Full as exc:
                    self._logger.exception(exc)
                    self._logger.warning(
                        'Lost CoT Event (queue full): "%s"', rendered_event)
            i += 1

    def _reset_local_buffer(self):
        self.local_buffer_adsb_msg = []
        self.local_buffer_adsb_ts = []
        self.local_buffer_commb_msg = []
        self.local_buffer_commb_ts = []

    async def run(self):
        self._logger.info(
            "Running ADSBNetWorker for data_type=%s", self.data_type)

        self._reset_local_buffer()
        decoder = pyModeS.streamer.decode.Decode()
        net_client = pyModeS.streamer.source.NetSource("x", 1, self.data_type)

        await self.msg_queue.put(
            adsbcot.hello_event().render(encoding='UTF-8', standalone=True))

        while 1:
            messages = []
            received = await self.net_queue.get()
            if not received:
                continue

            net_client.buffer.extend(received)
            if "beast" in self.data_type:
                messages = net_client.read_beast_buffer()
            elif "raw" in self.data_type:
                messages = net_client.read_raw_buffer()
            elif "skysense" in self.data_type:
                messages = net_client.read_skysense_buffer()

            self._logger.debug('len(msg)=%s', len(messages))

            if not messages:
                continue
            else:
                for msg, t in messages:
                    if len(msg) != 28:  # wrong data length
                        continue

                    df = pms.df(msg)

                    if df != 17:  # not ADSB
                        continue

                    if pms.crc(msg) != 0:  # CRC fail
                        continue

                    icao = pms.adsb.icao(msg)
                    tc = pms.adsb.typecode(msg)

                    if df == 17 or df == 18:
                        self.local_buffer_adsb_msg.append(msg)
                        self.local_buffer_adsb_ts.append(t)
                    elif df == 20 or df == 21:
                        self.local_buffer_commb_msg.append(msg)
                        self.local_buffer_commb_ts.append(t)
                    else:
                        continue

                if len(self.local_buffer_adsb_msg) > 1:
                    decoder.process_raw(
                        self.local_buffer_adsb_ts,
                        self.local_buffer_adsb_msg,
                        self.local_buffer_commb_ts,
                        self.local_buffer_commb_msg
                    )
                    self._reset_local_buffer()

                acs = decoder.get_aircraft()
                for k, v in acs.items():
                    lat = v.get("lat")
                    lon = v.get("lon")
                    flight = v.get("call", k)
                    alt_geom = v.get("alt")
                    gs = v.get("gs")
                    if lat and lon and flight and alt_geom and gs:
                        aircraft = [
                            {
                                "hex": k,
                                "lat": lat,
                                "lon": lon,
                                "flight": flight.replace("_", ""),
                                "alt_geom": alt_geom,
                                "gs": gs
                            }
                        ]
                        await self._put_msg_queue(aircraft)
                    else:
                        continue
