#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Greg Albrecht <oss@undef.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author:: Greg Albrecht W2GMD <oss@undef.net>
#

"""ADSBCOT Class Definitions."""

import asyncio
import logging

import aiohttp
import pytak
import adsbcot

# We won't use pyModeS if it isn't installed:
try:
    import pyModeS.streamer.source
    import pyModeS.streamer.decode
    import pyModeS as pms
except ImportError:
    pass


__author__ = "Greg Albrecht W2GMD <oss@undef.net>"
__copyright__ = "Copyright 2022 Greg Albrecht"
__license__ = "Apache License, Version 2.0"


class ADSBWorker(pytak.QueueWorker):

    """Reads ADS-B Data from inputs, renders to CoT, and puts on queue."""

    def __init__(self, queue, config):
        super().__init__(queue, config)
        _ = [x.setFormatter(adsbcot.LOG_FORMAT) for x in self._logger.handlers]
        self.uid_key: str = self.config.get("UID_KEY", "ICAO")

    async def handle_data(self, data: list) -> None:
        """
        Transforms Aircraft ADS-B data to CoT and puts it onto tx queue.
        """
        if not isinstance(data, list):
            self._logger.warning("Invalid aircraft data, should be a Python list.")
            return False

        if not data:
            self._logger.warning("Empty aircraft list")
            return False

        i = 1
        for craft in data:
            self._logger.debug("craft='%s'", craft)

            event = adsbcot.adsb_to_cot(craft, self.config)
            if not event:
                self._logger.debug("Empty COT Event for craft=%s", craft)
                i += 1
                continue

            self._logger.debug(
                "Handling %s/%s ICAO: %s Flight: %s Category: %s Registration: %s",
                i,
                len(data),
                craft.get("hex"),
                craft.get("flight"),
                craft.get("category"),
                craft.get("reg"),
            )
            await self.put_queue(event)
            i += 1

    async def get_dump1090_feed(self, url: str):
        """
        Polls the dump1090 JSON API and passes data to message handler.
        """
        async with aiohttp.ClientSession() as session:
            resp = await session.request(method="GET", url=url)
            resp.raise_for_status()

            json_resp = await resp.json()
            data = json_resp.get("aircraft")

            self._logger.info("Retrieved %s aircraft messages.", len(data))
            await self.handle_data(data)

    async def run(self, number_of_iterations=-1):
        """Runs this Thread, Reads from Pollers."""
        url: str = self.config.get("DUMP1090_URL")
        poll_interval: int = int(
            self.config.get("POLL_INTERVAL", adsbcot.DEFAULT_POLL_INTERVAL)
        )

        self._logger.info(
            "Using UID_KEY=%s & COT_STALE=%ss",
            self.uid_key,
            self.config.get("COT_STALE"),
        )

        while 1:
            self._logger.info("Polling every %ss: %s", url, poll_interval)
            await self.get_dump1090_feed(url)
            await asyncio.sleep(poll_interval)


class ADSBNetWorker(ADSBWorker):
    """Reads ADS-B Data from network, renders to COT, and puts on queue."""

    def __init__(
        self, queue, net_queue, config, data_type
    ):  # NOQA pylint: disable=too-many-arguments
        super().__init__(queue, config)
        self.net_queue = net_queue
        self.config = config
        self.data_type = data_type

        self.local_buffer_adsb_msg = []
        self.local_buffer_adsb_ts = []
        self.local_buffer_commb_msg = []
        self.local_buffer_commb_ts = []

    def _reset_local_buffer(self):
        """Resets Socket Buffers."""
        self.local_buffer_adsb_msg = []
        self.local_buffer_adsb_ts = []
        self.local_buffer_commb_msg = []
        self.local_buffer_commb_ts = []

    async def run(
        self, number_of_iterations=-1
    ):  # NOQA pylint: disable=too-many-locals, too-many-branches
        """Runs the main process loop."""
        self._logger.info("Running ADSBNetWorker for data_type='%s'", self.data_type)

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

            for msg, t_msg in messages:
                if len(msg) != 28:  # wrong data length
                    continue

                dl_fmt = pms.df(msg)

                if dl_fmt != 17:  # not ADSB
                    continue

                if pms.crc(msg) != 0:  # CRC fail
                    continue

                # icao = pms.adsb.icao(msg)
                # typecode = pms.adsb.typecode(msg)

                if dl_fmt in (17, 18):
                    self.local_buffer_adsb_msg.append(msg)
                    self.local_buffer_adsb_ts.append(t_msg)
                elif dl_fmt in (20, 21):
                    self.local_buffer_commb_msg.append(msg)
                    self.local_buffer_commb_ts.append(t_msg)
                else:
                    continue

            if len(self.local_buffer_adsb_msg) > 1:
                decoder.process_raw(
                    self.local_buffer_adsb_ts,
                    self.local_buffer_adsb_msg,
                    self.local_buffer_commb_ts,
                    self.local_buffer_commb_msg,
                )
                self._reset_local_buffer()

            acs = decoder.get_aircraft()
            for key, val in acs.items():
                # self._logger.debug("acs=%s", acs[k])
                lat = val.get("lat")
                lon = val.get("lon")
                flight = val.get("call", key)
                alt_geom = val.get("alt")
                gnds = val.get("gs")
                reg = val.get("r")
                trk = val.get("trk")
                # FIXME: Convert this to a filter()
                if (  # pylint: disable=too-many-boolean-expressions
                    lat and lon and flight and alt_geom and gnds and trk
                ):
                    data = [
                        {
                            "hex": key,
                            "lat": lat,
                            "lon": lon,
                            "flight": flight.replace("_", ""),
                            "alt_geom": alt_geom,
                            "gs": gnds,
                            "reg": reg,
                            "trk": trk,
                        }
                    ]
                    await self.handle_data(data)
                else:
                    continue


class ADSBNetReceiver:  # pylint: disable=too-few-public-methods
    """Reads ADS-B Data from network and puts on queue."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(adsbcot.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(adsbcot.LOG_LEVEL)
        _console_handler.setFormatter(adsbcot.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False
    logging.getLogger("asyncio").setLevel(adsbcot.LOG_LEVEL)

    def __init__(self, queue, config, url, data_type):
        self.queue = queue
        self.config = config
        self.url = url
        self.data_type = data_type

        if self.config.getboolean("DEBUG", False):
            _ = [x.setLevel(logging.DEBUG) for x in self._logger.handlers]

    async def run(self):
        """Runs the main process loop."""
        self._logger.info("Running %s for %s", self.__class__, self.url.geturl())

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

        reader, _ = await asyncio.open_connection(host, port)

        if self.data_type == "raw":
            while 1:
                received = await reader.readline()
                self.queue.put_nowait(received)
        elif self.data_type == "beast":
            while 1:
                received = await reader.read(4096)
                self.queue.put_nowait(received)
