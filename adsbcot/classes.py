#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADS-B Cursor-on-Target Class Definitions."""


import aiohttp
import asyncio
import logging

import pytak

import adsbcot

with_pymodes = False
try:
    import pyModeS.streamer.source
    import pyModeS.streamer.decode
    import pyModeS as pms
    with_pymodes = True
except ImportError:
    pass


__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2020 Orion Labs, Inc."
__license__ = "Apache License, Version 2.0"


class ADSBWorker(pytak.MessageWorker):

    """Reads ADS-B Data from inputs, renders to CoT, and puts on queue."""

    def __init__(self, event_queue, url, cot_stale, poll_interval: int = None):
        super().__init__(event_queue, url)
        self.poll_interval: int = int(poll_interval or adsbcot.DEFAULT_POLL_INTERVAL)
        self.url = url
        self.cot_stale = cot_stale
        self._logger.debug("cot_stale='%s'", self.cot_stale)

    async def handle_message(self, aircraft: list) -> None:
        """
        Transforms Aircraft AIS data to CoT and puts it onto tx queue.
        """
        if not isinstance(aircraft, list):
            self._logger.warning(
                "Invalid aircraft data, should be a Python list.")
            return False

        if not aircraft:
            self._logger.warning("Empty aircraft list")
            return False

        i = 1
        for craft in aircraft:
            self._logger.debug("craft='%s'", craft)
            event = adsbcot.adsb_to_cot(craft, stale=self.cot_stale)
            if not event:
                self._logger.debug(f"Empty CoT Event for craft={craft}")
                i += 1
                continue

            self._logger.debug(
                "Handling %s/%s ICAO: %s Flight: %s Category: %s",
                i, len(aircraft), craft.get("hex"), craft.get("flight"),
                craft.get("category"))
            await self._put_event_queue(event)
            i += 1

    async def _get_dump1090_feed(self):
        """
        Polls the dump1090 JSON API and passes data to message handler.
        """
        async with aiohttp.ClientSession() as session:
            resp = await session.request(method="GET", url=self.url.geturl())
            resp.raise_for_status()

            json_resp = await resp.json()
            aircraft = json_resp.get("aircraft")
            self._logger.debug(
                "Retrieved %s aircraft from %s",
                len(aircraft), self.url.geturl())

            await self.handle_message(aircraft)

    async def run(self):
        """Runs this Thread, Reads from Pollers."""
        self._logger.info(
            "Running ADSBWorker with URL '%s'", self.url.geturl())

        while 1:
            await self._get_dump1090_feed()
            await asyncio.sleep(self.poll_interval)


class ADSBNetWorker(ADSBWorker):

    def __init__(self, event_queue, net_queue, data_type, cot_stale):
        super().__init__(event_queue, None, cot_stale)
        self.net_queue = net_queue
        self.data_type = data_type

    def _reset_local_buffer(self):
        """Resets Socket Buffers."""
        self.local_buffer_adsb_msg = []
        self.local_buffer_adsb_ts = []
        self.local_buffer_commb_msg = []
        self.local_buffer_commb_ts = []

    async def run(self):
        self._logger.info(
            "Running ADSBNetWorker for data_type='%s'", self.data_type)

        self._reset_local_buffer()

        decoder = pyModeS.streamer.decode.Decode()
        net_client = pyModeS.streamer.source.NetSource("x", 1, self.data_type)

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

            self._logger.debug("Received %s messages", len(messages))

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
                    # self._logger.debug("acs=%s", acs[k])
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
                        await self.handle_message(aircraft)
                    else:
                        continue


class ADSBNetReceiver:

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(adsbcot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(adsbcot.LOG_LEVEL)
        _console_handler.setFormatter(adsbcot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger("asyncio").setLevel(adsbcot.LOG_LEVEL)

    def __init__(self, net_queue, url, data_type):
        self.net_queue = net_queue
        self.url = url
        self.data_type = data_type

    async def run(self):
        self._logger.info(
            "Running ADSBNetReceiver for URL=%s", self.url.geturl())

        if ":" in self.url.path:
            host, port = self.url.path.split(":")
        else:
            host = self.url.path
            if self.data_type == "raw":
                port = adsbcot.DEFAULT_DUMP1090_TCP_RAW_PORT
            elif self.data_type == "beast":
                port = adsbcot.DEFAULT_DUMP1090_TCP_BEAST_PORT
            else:
                raise Exception("Invalid data_type='%s'" % self.data_type)

        self._logger.debug("host=%s port=%s", host, port)

        reader, writer = await asyncio.open_connection(host, port)

        if self.data_type == "raw":
            while 1:
                received = await reader.readline()
                self.net_queue.put_nowait(received)
        elif self.data_type == "beast":
            while 1:
                received = await reader.read(4096)
                self.net_queue.put_nowait(received)

