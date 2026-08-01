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
from typing import Optional, Union
from urllib.parse import ParseResult, ParseResultBytes, urlparse

import aiohttp
import websockets
import pytak
import aircot
import adsbcot
import xml.etree.ElementTree as ET

try:
    import gpsd as _gpsd
except ImportError:
    _gpsd = None


# Note: inotify is optional and only functional on Linux systems.
try:
    from asyncinotify import Inotify, Mask
except (ImportError, AttributeError) as exc:
    warnings.warn(str(exc))
    warnings.warn("ADSBCOT ignoring ImportError for: asyncinotify")

# Skip importing pyModeS if it is not installed:
try:
    import pyModeS.streamer.source
    import pyModeS.streamer.decode
    import pyModeS as pms
except ImportError as exc:
    warnings.warn(str(exc))
    warnings.warn("ADSBCOT ignoring ImportError for: pyModeS")


class _NoStatus:
    """Stand-in for pytak.StatusWriter on a pytak too old to have one.

    AryaOS boxes are updated as packages, so this gateway can land on a host
    whose pytak predates StatusWriter (added in 7.4.0) -- the fleet is on
    7.3.13 today. Failing to import would take the gateway down over its
    telemetry helper, which is exactly backwards: moving CoT is the job,
    reporting on it is not.

    Degrading here is safe because it is VISIBLE. With nothing writing
    /run/adsbcot/status.json, the Cockpit plugin reports "no status from this
    gateway ... may be running a pytak too old to report status" rather than
    rendering an empty feed as though the sky were empty.
    """

    def count(self, *args, **kwargs) -> None:
        return None

    def record(self, *args, **kwargs) -> None:
        return None

    def set(self, *args, **kwargs) -> None:
        return None

    def write(self, *args, **kwargs) -> bool:
        return False


# Resolved at import so a missing StatusWriter is a startup-time decision
# rather than an AttributeError on the first aircraft.
_StatusWriter = getattr(pytak, "StatusWriter", None)


def make_status(app_name: str, version: str):
    """Return a status writer, or a no-op if this pytak has none."""
    if _StatusWriter is None:
        return _NoStatus()
    return _StatusWriter(app_name, version=version)


class ADSBWorker(pytak.QueueWorker):
    """Process ADS-B data from various sources, convert to CoT, and enqueue for transmission."""

    def __init__(self, queue, config) -> None:
        """Initialize this class."""
        super().__init__(queue, config)
        self.known_craft_db: Optional[dict] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.uid_key: str = self.config.get("UID_KEY", "ICAO")
        self.altitudes: dict = {}

        # Runtime status for Cockpit. systemd gives us /run/adsbcot via
        # RuntimeDirectory=, so this lands where the plugin looks for it.
        self.status = make_status("adsbcot", adsbcot.__version__)

        known_craft = self.config.get("KNOWN_CRAFT")
        if known_craft and os.path.exists(known_craft):
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            self.known_craft_db = aircot.read_known_craft(known_craft)

    async def _status_heartbeat(self, interval: float = 5.0) -> None:
        """Keep the status file fresh while no aircraft are being heard.

        A dish pointed at empty sky and a wedged gateway both produce zero
        CoT. The UI tells them apart by whether this file keeps changing, so
        an idle-but-healthy gateway MUST keep writing.

        Run as a separate task rather than folded into the feed loop because
        the feed loop's period is the operator's choice (POLL_INTERVAL is 30s+
        for API feeds, and the Beast/inotify paths block on a reader with no
        period at all). Neither can be relied on for a 5s heartbeat, and
        neither should be slowed down to provide one.
        """
        while True:
            await asyncio.sleep(interval)
            self.status.write(force=True)

    async def handle_data(self, data: Union[list, dict]) -> None:
        """Handle Data from ADS-B receiver: Render to CoT, put on TX queue."""
        if not data:
            self._logger.warning("Empty aircraft list")
            return

        if isinstance(data, list):
            lod = len(data)
            i = 1
            # How many aircraft this receiver currently has in view. Reported
            # separately from the counters because it is a level, not a total:
            # "12 aircraft right now" is the number an operator checks an
            # antenna against, and lifetime `rx` cannot answer it.
            self.status.set(tracked=lod)
            for craft in data:
                i += 1
                icao = await self.process_craft(craft)
                self._logger.debug("Handling %s/%s ICAO: %s", i, lod, icao)
        elif isinstance(data, dict):
            # Handle a single aircraft data dictionary
            icao = await self.process_craft(data)
            self._logger.debug("Handling ICAO: %s", icao)

    async def process_craft(self, craft: dict) -> Optional[str]:
        """Process a single aircraft data dictionary.
        Parameters
        ----------
        craft : `dict`
            Dictionary containing aircraft data.

        Returns
        -------
        Optional[str]
            The ICAO code of the aircraft, or None if not found.
        """
        if not isinstance(craft, dict):
            # Not an aircraft record at all -- deliberately NOT counted as
            # received, so a malformed feed cannot inflate `rx` into looking
            # like healthy traffic.
            self._logger.warning("Aircraft list item was not a Python `dict`.")
            return None

        self.status.count("rx")

        icao: Union[str, None] = None
        icao_int: str = craft.get("Icao_addr", "")  # Stratux: 24-bit ICAO address
        if icao_int:
            icao = aircot.icao_int_to_hex(icao_int)
        else:
            icao = craft.get("hex", craft.get("icao", ""))

        if icao:
            icao = icao.strip().upper()
        else:
            self._logger.warning("No ICAO code found in craft data.")
            self.status.count("no_icao")
            self.status.write()
            return None

        if "~" in icao:
            if not self.config.getboolean("INCLUDE_TISB"):
                self._logger.debug("Skipping TIS-B data: %s", icao)
                # Counted, not logged per-craft: in TIS-B-rich airspace this
                # fires constantly and would drown the journal, but an
                # operator wondering "why do I see so little" needs to know
                # the filter is what is eating the traffic.
                self.status.count("filtered_tisb")
                self.status.write()
                return None
        else:
            if self.config.getboolean("TISB_ONLY"):
                self._logger.debug("Skipping non-TIS-B data: %s", icao)
                self.status.count("filtered_tisb")
                self.status.write()
                return None

        known_craft: dict = aircot.get_known_craft(self.known_craft_db, icao, "HEX")

        # Skip if we're using known_craft CSV and this Craft isn't found:
        if (
            self.known_craft_db
            and not known_craft
            and not self.config.getboolean("INCLUDE_ALL_CRAFT")
        ):
            self._logger.debug("Skipping unknown craft: %s", icao)
            self.status.count("filtered_unknown")
            self.status.write()
            return None

        ref_alts = self.calc_altitude(craft)
        craft.update(ref_alts)

        if not craft:
            self._logger.debug("No altitude data for craft: %s", icao)
            return None

        event: Optional[bytes] = adsbcot.adsb_to_cot(craft, self.config, known_craft)

        # Record EVERY aircraft that got this far, plotted or not. A dump1090
        # feed routinely carries Mode S returns with a hex and a callsign but
        # no position yet, and a feed showing only plotted aircraft would sit
        # near-empty on a receiver that is hearing plenty -- which reads as a
        # dead antenna. The `placed` flag keeps both facts visible.
        self.status.record(
            icao=icao,
            flight=str(craft.get("flight", craft.get("Tail", ""))).strip() or None,
            alt=craft.get("alt_geom", craft.get("alt_baro")),
            speed=craft.get("gs", craft.get("Speed")),
            placed=event is not None,
        )

        if not event:
            self._logger.debug("Empty COT Event for craft=%s", craft)
            # Overwhelmingly "no lat/lon yet", not an error.
            self.status.count("no_position")
            self.status.write()
            return None

        self.status.count("emitted")
        self.status.write()
        await self.put_queue(event)
        return icao

    def calc_altitude(self, craft: dict) -> dict:
        """Calculate altitude based on barometric and geometric altitude."""
        alt_baro = craft.get("alt_baro", "")
        alt_geom = craft.get("alt_geom", "")

        if not alt_baro:
            return {}

        if alt_baro == "ground":
            return {}

        alt_baro = float(alt_baro)
        if alt_geom:
            self.altitudes["alt_geom"] = float(alt_geom)
            self.altitudes["alt_baro"] = alt_baro
        elif "alt_baro" in self.altitudes and "alt_geom" in self.altitudes:
            ref_alt_baro = float(self.altitudes["alt_baro"])
            alt_baro_offset = alt_baro - ref_alt_baro
            return {
                "x_alt_baro_offset": alt_baro_offset,
                "x_alt_geom": ref_alt_baro + alt_baro_offset,
            }

        return {}

    async def get_feed(self, url: bytes) -> None:
        """Poll the ADS-B feed and pass data to the data handler."""
        if self.session is None or self.session.closed:
            self._logger.error("Session is closed, cannot proceed.")
            return

        url_b = str(url)

        api_key: str = self.config.get("API_KEY", "")
        headers = {"api-auth": api_key}

        # Support for either direct ADSBX API, or RapidAPI:
        if "rapidapi" in url_b.lower():
            headers = {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": self.config.get(
                    "RAPIDAPI_HOST", adsbcot.DEFAULT_RAPIDAPI_HOST
                ),
            }

        async with self.session.get(url_b, headers=headers) as resp:
            if resp.status != 200:
                response_content = await resp.text()
                self._logger.error("Received HTTP Status %s for %s", resp.status, url)
                self._logger.error(response_content)
                return

            json_resp = await resp.json(content_type=None)
            if json_resp is None:
                self._logger.debug("Empty JSON response from %s", url)
                return

            data = json_resp.get("aircraft", json_resp.get("ac"))
            if data is None:
                self._logger.debug("No aircraft data returned from %s", url)
                return

            self._logger.info(
                "Retrieved %s ADS-B aircraft messages.", str(len(data) or "No")
            )
            await self.handle_data(data)

    async def get_file_feed(self, feed_url: ParseResultBytes) -> None:
        """Read data from an aircraft JSON file."""
        jdata: dict = {}
        feed_data: str = ""

        with open(feed_url.path, "r", encoding="UTF-8") as feed_fd:
            feed_data = feed_fd.read()

        if not feed_data:
            self._logger.info("No data returned from FEED_URL=%s", feed_url.path)
            return

        jdata = json.loads(feed_data)

        data = jdata.get("aircraft", jdata.get("ac"))
        if not data:
            self._logger.info(
                "No aircraft data returned from FEED_URL=%s", feed_url.path
            )
            return

        self._logger.info(
            "Retrieved %s ADS-B aircraft messages.", str(len(data) or "No")
        )
        await self.handle_data(data)

    async def run(self, _=-1) -> None:
        """Run this Thread, Reads from Pollers."""

        url: Optional[bytes] = self.config.get("FEED_URL")
        if not url or url == "":
            raise ValueError("Please specify a FEED_URL.")

        poll_interval: Union[int, str, None] = self.config.get("POLL_INTERVAL")
        if poll_interval == "" or poll_interval is None:
            self._logger.info(
                "POLL_INTERVAL not set, using default of %s seconds.",
                adsbcot.DEFAULT_POLL_INTERVAL,
            )
            poll_interval = adsbcot.DEFAULT_POLL_INTERVAL

        self._logger.info(
            "Running %s at %ss for %s", self.__class__, poll_interval, url
        )

        known_craft: bytes = self.config.get("KNOWN_CRAFT", "")
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

        # Write once, before any aircraft arrive. Without this the management
        # UI shows "no status from this gateway" until the first contact --
        # indistinguishable from a gateway that failed to start, which on a
        # quiet band or a bad antenna is exactly when someone is looking.
        self.status.set(feed=str(url))
        self.status.write(force=True)

        heartbeat = asyncio.ensure_future(self._status_heartbeat())
        try:
            await self._run_feed(url, feed_url, poll_interval)
        finally:
            heartbeat.cancel()

    async def _run_feed(self, url, feed_url: ParseResultBytes, poll_interval) -> None:
        """Dispatch to the reader for this feed's URL scheme."""
        url_scheme = str(feed_url.scheme)

        if "http" in url_scheme:
            async with aiohttp.ClientSession() as self.session:
                while 1:
                    self._logger.info(
                        "%s polling every %ss: %s", self.__class__, poll_interval, url
                    )
                    await self.get_feed(url)
                    await asyncio.sleep(int(poll_interval))
        elif "ws" in url_scheme:
            try:
                async with websockets.connect(url) as websocket:
                    self._logger.info("Connected to: %s", url)
                    async for message in websocket:
                        self._logger.debug("message=%s", message)
                        if message:
                            j_event = json.loads(message)
                            await self.handle_data(j_event)
            except websockets.exceptions.ConnectionClosedError:
                self._logger.warning("Websocket closed, reconnecting...")
                await asyncio.sleep(2)
        elif "file" in url_scheme:
            if importlib.util.find_spec("asyncinotify") is None:
                self._logger.info("asyncinotify not installed, using file polling.")
                while 1:
                    self._logger.info(
                        "%s polling every %ss: %s", self.__class__, poll_interval, url
                    )
                    await self.get_file_feed(feed_url)
                    await asyncio.sleep(int(poll_interval))
            else:
                with Inotify() as inotify:
                    path = str(feed_url.path)
                    inotify.add_watch(
                        Path(path).parents[0],
                        Mask.MODIFY | Mask.CREATE | Mask.MOVE | Mask.MOVED_TO,
                    )

                    async for event in inotify:
                        if event.mask & Mask.IGNORED:
                            raise RuntimeError("inotify watch was removed.")
                        if str(event.path) == path:
                            await self.get_file_feed(feed_url)


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

        # Same reasoning as ADSBWorker.run(): report before traffic, and keep
        # reporting while idle. The heartbeat is a task rather than a timer in
        # this loop because the loop blocks on net_queue.get() -- with a silent
        # receiver it would never come round to write anything.
        self.status.set(feed=str(self.config.get("FEED_URL", "")))
        self.status.write(force=True)
        heartbeat = asyncio.ensure_future(self._status_heartbeat())

        try:
            await self._run_decoder(decoder, net_client)
        finally:
            heartbeat.cancel()

    async def _run_decoder(self, decoder, net_client) -> None:
        """Read framed Mode S from the network queue and decode to aircraft."""
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
            # Collected into one batch rather than handed over one aircraft at
            # a time so the status surface can report how many aircraft the
            # decoder currently holds. Per-craft calls would each report a
            # "tracked" count of 1, which is a number, just not a true one.
            crafts: list = []
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
                    crafts.append(_data)

            if crafts:
                await self.handle_data(crafts)


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


class xFileWatcher(pytak.QueueWorker):
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
        if not self.session:
            self._logger.warning("No aiohttp session available.")
            return

        async with self.session.get(url) as resp:
            if resp.status != 200:
                response_content = await resp.text()
                self._logger.error("Received HTTP Status %s for %s", resp.status, url)
                self._logger.error(response_content)
                return

            json_resp = await resp.json(content_type=None)
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
        url: bytes = self.config.get("FEED_URL", adsbcot.DEFAULT_FEED_URL)
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


class SensorWorker(pytak.QueueWorker):
    """Periodic sensor CoT heartbeat. Sources position from gpsd, config, or null island."""

    async def run(self, _=-1) -> None:
        period = int(self.config.get(
            "SENSOR_KEEPALIVE_PERIOD", adsbcot.DEFAULT_SENSOR_KEEPALIVE_PERIOD))
        self._logger.info(
            "Running SensorWorker (period=%ds, gpsd=%s)", period, _gpsd is not None)
        while True:
            lat, lon, hae, ce, le = await self._get_position()
            cot = adsbcot.gen_sensor_cot(self.config, lat, lon, hae, ce, le)
            if cot is not None:
                await self.put_queue(ET.tostring(cot))
            await asyncio.sleep(period)

    async def _get_position(self):
        if _gpsd is not None:
            try:
                result = await asyncio.to_thread(self._poll_gpsd)
                if result is not None:
                    return result
            except Exception as exc:
                self._logger.debug("gpsd unavailable: %s", exc)
        lat = float(self.config.get("SENSOR_LAT") or adsbcot.DEFAULT_SENSOR_LAT)
        lon = float(self.config.get("SENSOR_LON") or adsbcot.DEFAULT_SENSOR_LON)
        hae = float(self.config.get("SENSOR_HAE") or adsbcot.DEFAULT_SENSOR_HAE)
        return lat, lon, hae, "9999999.0", "9999999.0"

    @staticmethod
    def _poll_gpsd():
        _gpsd.connect()
        packet = _gpsd.get_current()
        if packet.mode < 2:
            return None
        try:
            lat, lon = packet.position()
        except Exception:
            return None
        try:
            hae = packet.altitude()
        except Exception:
            hae = 0.0
        ce = str(getattr(packet, "error", {}).get("x", "9999999.0") or "9999999.0")
        le = str(getattr(packet, "error", {}).get("v", "9999999.0") or "9999999.0")
        return lat, lon, hae, ce, le
