#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright Sensors & Signals LLC https://www.snstac.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""ADSBCOT Class Definitions."""

import asyncio
import importlib.util
import json
import os
import warnings

from pathlib import Path
from typing import Optional
from urllib.parse import ParseResult, ParseResultBytes, urlparse

import aiohttp
import pytak
import aircot
import adsbcot


# We don't require inotify, as it only would work on Linux
try:
    from asyncinotify import Inotify, Mask
except ImportError as exc:
    warnings.warn(str(exc))
    warnings.warn("ADSBCOT ignoring ImportError for: asyncinotify")

# We won't use pyModeS if it isn't installed:
try:
    import pyModeS.streamer.source
    import pyModeS.streamer.decode
    import pyModeS as pms
except ImportError as exc:
    warnings.warn(str(exc))
    warnings.warn("ADSBCOT ignoring ImportError for: pyModeS")


__author__ = "Greg Albrecht <gba@snstac.com>"
__copyright__ = "Copyright Sensors & Signals LLC https://www.snstac.com"
__license__ = "Apache License, Version 2.0"


class ADSBWorker(pytak.QueueWorker):
    """Read ADS-B Data from inputs, serialize to CoT, and put on TX queue."""

    def __init__(self, queue, config) -> None:
        """Initialize this class."""
        super().__init__(queue, config)
        self.known_craft_db: Optional[dict] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.uid_key: str = self.config.get("UID_KEY", "ICAO")

        known_craft = self.config.get("KNOWN_CRAFT")
        if known_craft and os.path.exists(known_craft):
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            self.known_craft_db = aircot.read_known_craft(known_craft)

    async def handle_data(self, data: list) -> None:
        """Handle Data from ADS-B receiver: Render to CoT, put on TX queue.

        Parameters
        ----------
        data : `list[dict, ]`
            List of craft data as key/value arrays.
        """
        if not isinstance(data, list):
            self._logger.warning("Invalid aircraft data, should be a Python `list`.")
            return

        if not data:
            self._logger.warning("Empty aircraft list")
            return

        lod = len(data)
        i = 1
        for craft in data:
            i += 1
            if not isinstance(craft, dict):
                self._logger.warning("Aircraft list item was not a Python `dict`.")
                continue

            icao: str = craft.get("hex", "")
            if icao:
                icao = icao.strip().upper()
            else:
                continue

            if "~" in icao:
                if not self.config.getboolean("INCLUDE_TISB"):
                    continue
            else:
                if self.config.getboolean("TISB_ONLY"):
                    continue

            known_craft: dict = aircot.get_known_craft(self.known_craft_db, icao, "HEX")

            # Skip if we're using known_craft CSV and this Craft isn't found:
            if (
                self.known_craft_db
                and not known_craft
                and not self.config.getboolean("INCLUDE_ALL_CRAFT")
            ):
                continue

            event: Optional[bytes] = adsbcot.adsb_to_cot(
                craft, self.config, known_craft
            )

            if not event:
                self._logger.debug("Empty COT Event for craft=%s", craft)
                continue

            self._logger.debug("Handling %s/%s ICAO: %s", i, lod, icao)
            await self.put_queue(event)

    async def get_feed(self, url: bytes) -> None:
        """Poll the ADS-B feed and pass data to the data handler."""
        if not self.session:
            return

        url_b = str(url)
        async with self.session.get(url_b) as resp:
            if resp.status != 200:
                response_content = await resp.text()
                self._logger.error("Received HTTP Status %s for %s", resp.status, url)
                self._logger.error(response_content)
                return

            json_resp = await resp.json()
            if json_resp is None:
                return

            data = json_resp.get("aircraft", json_resp.get("ac"))
            if data is None:
                return

            self._logger.info(
                "Retrieved %s ADS-B aircraft messages.", str(len(data) or "No")
            )
            await self.handle_data(data)

    async def run(self, _=-1) -> None:
        """Run this Thread, Reads from Pollers."""
        dump1090_url: bytes = self.config.get("DUMP1090_URL", "")
        if dump1090_url:
            warnings.warn(
                "DUMP1090_URL setting is DEPRECATED. Please use FEED_URL instead."
            )

        url: bytes = self.config.get("FEED_URL", dump1090_url)
        if not url:
            raise ValueError("Please specify a FEED_URL.")

        self._logger.info("Running %s", self.__class__)

        known_craft: bytes = self.config.get("KNOWN_CRAFT", "")
        poll_interval: bytes = self.config.get(
            "POLL_INTERVAL", adsbcot.DEFAULT_POLL_INTERVAL
        )

        if known_craft:
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            self.known_craft_db = aircot.read_known_craft(known_craft)

        alt_upper: int = int(self.config.get("ALT_UPPER", "0"))
        alt_lower: int = int(self.config.get("ALT_LOWER", "0"))
        if alt_upper or alt_lower:
            self._logger.info(
                "Using Altitude Filters: Upper = %s, Lower = %s", alt_upper, alt_lower
            )

        feed_url: ParseResultBytes = urlparse(url)

        url_scheme = str(feed_url.scheme)

        if "http" in url_scheme:
            async with aiohttp.ClientSession() as self.session:
                while 1:
                    self._logger.info(
                        "%s polling every %ss: %s", self.__class__, poll_interval, url
                    )
                    await self.get_feed(url)
                    await asyncio.sleep(int(poll_interval))
        elif "file" in url_scheme:
            if importlib.util.find_spec("asyncinotify") is None:
                while 1:
                    self._logger.info(
                        "%s polling every %ss: %s", self.__class__, poll_interval, url
                    )
                    await self.get_file_feed(url)
                    await asyncio.sleep(int(poll_interval))
            else:
                with Inotify() as inotify:
                    path = str(feed_url.path)
                    inotify.add_watch(
                        Path(path).parents[0],
                        Mask.MODIFY | Mask.CREATE | Mask.MOVE | Mask.MOVED_TO,
                    )

                    async for event in inotify:
                        if str(event.path) == path:
                            await self.get_file_feed(feed_url)

    async def get_file_feed(self, feed_url) -> None:
        """Read data from an aircraft JSON file."""
        jdata = {}
        with open(feed_url.path, "r", encoding="UTF-8") as feed_fd:
            jdata = json.loads(feed_fd.read())

        data = jdata.get("aircraft", jdata.get("ac"))
        if data is None:
            return

        self._logger.info(
            "Retrieved %s ADS-B aircraft messages.", str(len(data) or "No")
        )
        await self.handle_data(data)


class ADSBNetWorker(ADSBWorker):
    """Read ADS-B Data from network, renders to COT, and puts on queue."""

    def __init__(
        self, queue, net_queue, config, data_type
    ):  # NOQA pylint: disable=too-many-arguments
        """Initialize this class."""
        super().__init__(queue, config)
        self.net_queue = net_queue
        self.config = config
        self.data_type = data_type

        self.local_buffer_adsb_msg = []
        self.local_buffer_adsb_ts = []
        self.local_buffer_commb_msg = []
        self.local_buffer_commb_ts = []

    def _reset_local_buffer(self):
        """Reset Socket Buffers."""
        self.local_buffer_adsb_msg = []
        self.local_buffer_adsb_ts = []
        self.local_buffer_commb_msg = []
        self.local_buffer_commb_ts = []

    async def run(
        self, _=-1
    ) -> None:  # NOQA pylint: disable=too-many-locals, too-many-branches
        """Run the main process loop."""
        self._logger.info(
            "Running %s for data_type: %s", self.__class__, self.data_type
        )

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
                _data: dict = {
                    "hex": key,
                    "lat": val.get("lat"),
                    "lon": val.get("lon"),
                    "flight": val.get("call", key).replace("_", ""),
                    "alt_geom": val.get("alt"),
                    "gs": val.get("gs"),
                    "reg": val.get("r"),
                    "trk": val.get("track", val.get("trk")),
                }
                if all(_data):
                    await self.handle_data([_data])


class ADSBNetReceiver(pytak.QueueWorker):  # pylint: disable=too-few-public-methods
    """Read ADS-B Data from network and puts on queue."""

    def __init__(self, queue, config, data_type) -> None:
        """Initialize this class."""
        super().__init__(queue, config)
        self.data_type: str = data_type

    async def run(self, _=-1) -> None:
        """Run the main process loop."""
        url: ParseResult = urlparse(self.config.get("FEED_URL"))

        self._logger.info("Running %s for %s", self.__class__, url.geturl())

        if ":" in url.netloc:
            host, port = url.netloc.split(":")
        else:
            host = url.netloc
            if self.data_type == "raw":
                port = adsbcot.DEFAULT_TCP_RAW_PORT
            elif self.data_type == "beast":
                port = adsbcot.DEFAULT_TCP_BEAST_PORT
            else:
                raise ValueError(f"Invalid data_type='{self.data_type}'")

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


class FileWatcher(pytak.QueueWorker):
    """Read ADS-B Data from a file, serialize to CoT, and put on TX queue."""

    def __init__(self, queue, config) -> None:
        """Initialize this class."""
        super().__init__(queue, config)
        self.known_craft_db = None
        self.session = None
        self.uid_key: str = self.config.get("UID_KEY", "ICAO")

        known_craft = self.config.get("KNOWN_CRAFT")
        if known_craft:
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            self.known_craft_db = aircot.read_known_craft(known_craft)

    async def handle_data(self, data: list) -> None:
        """Handle Data from ADS-B receiver: Render to CoT, put on TX queue.

        Parameters
        ----------
        data : `list[dict, ]`
            List of craft data as key/value arrays.
        """
        if not isinstance(data, list):
            self._logger.warning("Invalid aircraft data, should be a Python `list`.")
            return

        if not data:
            self._logger.warning("Empty aircraft list")
            return

        lod = len(data)
        i = 1
        for craft in data:
            i += 1
            if not isinstance(craft, dict):
                self._logger.warning("Aircraft list item was not a Python `dict`.")
                continue

            icao: str = craft.get("hex", "")
            if icao:
                icao = icao.strip().upper()
            else:
                continue

            if "~" in icao:
                if not self.config.getboolean("INCLUDE_TISB"):
                    continue
            else:
                if self.config.getboolean("TISB_ONLY"):
                    continue

            known_craft: dict = aircot.get_known_craft(self.known_craft_db, icao, "HEX")

            # Skip if we're using known_craft CSV and this Craft isn't found:
            if (
                self.known_craft_db
                and not known_craft
                and not self.config.getboolean("INCLUDE_ALL_CRAFT")
            ):
                continue

            event: Optional[bytes] = adsbcot.adsb_to_cot(
                craft, self.config, known_craft
            )

            if not event:
                self._logger.debug("Empty COT Event for craft=%s", craft)
                continue

            self._logger.debug("Handling %s/%s ICAO: %s", i, lod, icao)
            await self.put_queue(event)

    async def get_feed(self, url: bytes) -> None:
        """Poll the ADS-B feed and pass data to the data handler."""
        async with self.session.get(url) as resp:
            if resp.status != 200:
                response_content = await resp.text()
                self._logger.error("Received HTTP Status %s for %s", resp.status, url)
                self._logger.error(response_content)
                return

            json_resp = await resp.json()
            if json_resp is None:
                return

            data = json_resp.get("aircraft", json_resp.get("ac"))
            if data is None:
                return

            self._logger.info(
                "Retrieved %s ADS-B aircraft messages.", str(len(data) or "No")
            )
            await self.handle_data(data)

    async def run(self, _=-1) -> None:
        """Run this Thread, Reads from Pollers."""
        dump1090_url: bytes = self.config.get("DUMP1090_URL", "")
        if dump1090_url:
            warnings.warn(
                "DUMP1090_URL setting is DEPRECATED. Please use FEED_URL instead."
            )

        url: bytes = self.config.get("FEED_URL", dump1090_url)
        if not url:
            raise ValueError("Please specify a FEED_URL.")

        self._logger.info("Running %s", self.__class__)

        known_craft: bytes = self.config.get("KNOWN_CRAFT", "")
        poll_interval: bytes = self.config.get(
            "POLL_INTERVAL", adsbcot.DEFAULT_POLL_INTERVAL
        )

        if known_craft:
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            self.known_craft_db = aircot.read_known_craft(known_craft)

        async with aiohttp.ClientSession() as self.session:
            while 1:
                self._logger.info(
                    "%s polling every %ss: %s", self.__class__, poll_interval, url
                )
                await self.get_feed(url)
                await asyncio.sleep(int(poll_interval))
