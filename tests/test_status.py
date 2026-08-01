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

"""Tests for the ADSBCOT runtime status surface.

These assert what an operator would actually read off the Cockpit panel:
that a receiver hearing Mode S but no positions looks different from a dead
antenna, and that a filter eating the traffic is visible as a filter.

They drive the coroutines with asyncio.run() rather than pytest-asyncio. That
is not a style choice: pytest-asyncio is not installed in this environment,
and bare `async def` tests are SKIPPED by pytest while still being reported in
the run -- this repo already has ten such tests, and they cannot fail. These
must be able to.
"""

import asyncio
import json
import os

from configparser import ConfigParser

import pytest

import pytak

import adsbcot
from adsbcot.classes import ADSBWorker

# A real dump1090 aircraft record with a position.
CRAFT_PLOTTED = {
    "hex": "a9ee47",
    "flight": "N739UL  ",
    "alt_baro": 3700,
    "alt_geom": 3750,
    "gs": 79.5,
    "lat": 37.836449,
    "lon": -122.030281,
    "track": 50.1,
    "category": "A1",
}

# The other common dump1090 record: heard, identified, not yet located. A
# receiver can hold a lot of these while working perfectly.
CRAFT_NO_POSITION = {
    "hex": "ab1644",
    "flight": "UAL1234 ",
    "alt_baro": 3700,
    "squawk": "3514",
}

# TIS-B: rebroadcast ground-station traffic, marked with a tilde.
CRAFT_TISB = {
    "hex": "~a9ee47",
    "flight": "TISB0001",
    "alt_baro": 5000,
    "lat": 37.8,
    "lon": -122.0,
}

# No ICAO address at all -- received, but not an aircraft we can name.
CRAFT_NO_ICAO = {"alt_baro": 3700, "gs": 120.0}


needs_statuswriter = pytest.mark.skipif(
    not hasattr(pytak, "StatusWriter"),
    reason="installed pytak predates StatusWriter",
)

# Separate from the above: adsbcot has required pytak >= 7.3.12 for
# pytak.cot_event() since long before StatusWriter existed, so a pytak old
# enough to lack it cannot build CoT at all. Tests that need a real CoT event
# say so rather than failing for a reason that has nothing to do with status.
needs_cot_event = pytest.mark.skipif(
    not hasattr(pytak, "cot_event"),
    reason="installed pytak predates pytak.cot_event (adsbcot needs >= 7.3.12)",
)


async def _noop_put(event):
    return None


def _config(**overrides):
    parser = ConfigParser()
    parser.read_dict(
        {
            "DEFAULT": {
                "INCLUDE_TISB": "false",
                "TISB_ONLY": "false",
                "INCLUDE_ALL_CRAFT": "true",
                **overrides,
            }
        }
    )
    return parser["DEFAULT"]


def _build_worker(tmp_path=None, **overrides):
    """Build an ADSBWorker. MUST be called from inside a running event loop.

    asyncio.Queue() binds to the current event loop on Python < 3.10, and
    asyncio.run() leaves no current loop behind when it returns -- so building
    a worker at test-body level works locally on 3.13 and then fails in CI on
    3.9 with "There is no current event loop", but only in whichever test
    happens to run after the first asyncio.run(). Building inside the loop is
    portable across 3.9-3.13 and not order-dependent.
    """
    worker = ADSBWorker(asyncio.Queue(), _config(**overrides))
    if tmp_path is not None:
        worker.status = pytak.StatusWriter(
            "adsbcot-test", path=str(tmp_path / "status.json")
        )
    worker.put_queue = _noop_put
    return worker


@needs_statuswriter
class TestStatusSurface:
    """The data the Cockpit plugin reads."""

    def _worker(self, tmp_path, action=None, **overrides):
        """Build a worker and run `action(worker)` in one event loop."""
        built = {}

        async def _main():
            worker = _build_worker(tmp_path, **overrides)
            built["worker"] = worker
            if action is not None:
                await action(worker)

        asyncio.run(_main())
        return built["worker"]

    def _doc(self, worker):
        with open(worker.status.path, encoding="utf-8") as handle:
            return json.load(handle)

    def test_plotted_aircraft_is_marked_placed(self, tmp_path):
        worker = self._worker(tmp_path, lambda w: w.process_craft(dict(CRAFT_PLOTTED)))

        doc = self._doc(worker)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["emitted"] == 1
        entry = doc["recent"][0]
        assert entry["icao"] == "A9EE47"
        assert entry["flight"] == "N739UL"
        assert entry["alt"] == 3750
        assert entry["speed"] == 79.5
        assert entry["placed"] is True

    def test_positionless_aircraft_still_appears_in_the_feed(self, tmp_path):
        """A receiver hearing Mode S but no positions is NOT a dead receiver.

        If the feed only showed plotted aircraft, this case would render an
        empty panel on working hardware -- which an operator reads as a fault
        and starts swapping antennas over.
        """
        worker = self._worker(
            tmp_path, lambda w: w.process_craft(dict(CRAFT_NO_POSITION))
        )

        doc = self._doc(worker)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["no_position"] == 1
        assert "emitted" not in doc["counters"]
        entry = doc["recent"][0]
        assert entry["icao"] == "AB1644"
        assert entry["flight"] == "UAL1234"
        assert entry["placed"] is False

    def test_craft_without_icao_counted_but_not_shown_as_a_contact(self, tmp_path):
        """It was received; it is not an aircraft we can name."""
        worker = self._worker(tmp_path, lambda w: w.process_craft(dict(CRAFT_NO_ICAO)))

        doc = self._doc(worker)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["no_icao"] == 1
        assert doc["recent"] == []

    def test_non_dict_feed_item_is_not_counted_as_received(self, tmp_path):
        """Garbage in the feed is not an aircraft, and must not inflate `rx`."""
        worker = self._worker(tmp_path, lambda w: w.process_craft("not-an-aircraft"))
        assert not os.path.exists(worker.status.path)

    def test_tisb_filter_is_visible_as_a_filter(self, tmp_path):
        """"Why am I seeing so little traffic" must be answerable from the UI."""
        worker = self._worker(
            tmp_path,
            lambda w: w.process_craft(dict(CRAFT_TISB)),
            INCLUDE_TISB="false",
        )

        doc = self._doc(worker)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["filtered_tisb"] == 1
        assert "emitted" not in doc["counters"]

    def test_known_craft_filter_is_visible_as_a_filter(self, tmp_path):
        # A KNOWN_CRAFT CSV that does not list this aircraft, in the shape
        # aircot.read_known_craft() produces.
        def _filtered(worker):
            worker.known_craft_db = {"hex_index": {"DEADBE": {"TYPE": "a-f-A"}}}
            return worker.process_craft(dict(CRAFT_PLOTTED))

        worker = self._worker(tmp_path, _filtered, INCLUDE_ALL_CRAFT="false")

        doc = self._doc(worker)
        assert doc["counters"]["rx"] == 1
        assert doc["counters"]["filtered_unknown"] == 1
        assert "emitted" not in doc["counters"]

    def test_tracked_reports_aircraft_currently_in_view(self, tmp_path):
        """The number an operator checks an antenna against."""
        worker = self._worker(
            tmp_path,
            lambda w: w.handle_data([dict(CRAFT_PLOTTED), dict(CRAFT_NO_POSITION)]),
        )

        # Writes are rate-limited to once a second, so two aircraft handled in
        # the same second leave the file holding the first one's figures. That
        # is by design -- a busy feed must not spend its time serialising JSON
        # -- and the run loop's 5s heartbeat is what reconciles it. Forcing the
        # write here stands in for that heartbeat.
        worker.status.write(force=True)
        doc = self._doc(worker)
        assert doc["tracked"] == 2
        assert doc["counters"]["rx"] == 2
        assert doc["counters"]["emitted"] == 1
        assert doc["counters"]["no_position"] == 1

    def test_worker_publishes_under_the_package_name_and_version(self):
        """Consumers read /run/adsbcot/status.json by that exact name.

        Get the app name wrong and the gateway writes a status file nobody is
        watching, which presents identically to writing none at all.
        """
        async def _main():
            return _build_worker()

        worker = asyncio.run(_main())
        assert worker.status.app_name == "adsbcot"
        assert worker.status.version == adsbcot.__version__
        assert worker.status.path.endswith(os.path.join("adsbcot", "status.json"))


class TestStatusDegradesVisibly:
    """A pytak without StatusWriter must not take the gateway down.

    The fleet runs pytak 7.3.13, which has no StatusWriter at all, so this is
    the path most boxes take today -- not a theoretical fallback.
    """

    def test_no_op_status_when_pytak_is_too_old(self, monkeypatch):
        from adsbcot import classes

        monkeypatch.setattr(classes, "_StatusWriter", None)
        status = classes.make_status("adsbcot", "0.1.0")

        # Every call the worker makes must be safe on the stand-in.
        status.count("rx")
        status.record(icao="A9EE47", placed=True)
        status.set(tracked=1)
        assert status.write() is False

    @needs_cot_event
    def test_worker_still_processes_craft_without_a_status_writer(self, monkeypatch):
        """The gateway's job is CoT, not telemetry. Losing one keeps the other."""
        from adsbcot import classes

        monkeypatch.setattr(classes, "_StatusWriter", None)

        sent = []
        seen = {}

        async def _main():
            worker = _build_worker()
            seen["status"] = worker.status

            async def _capture(event):
                sent.append(event)

            worker.put_queue = _capture
            return await worker.process_craft(dict(CRAFT_PLOTTED))

        icao = asyncio.run(_main())
        assert isinstance(seen["status"], classes._NoStatus)
        assert icao == "A9EE47"
        assert len(sent) == 1

    def test_real_writer_used_when_available(self):
        from adsbcot import classes

        if classes._StatusWriter is None:
            pytest.skip("installed pytak has no StatusWriter")
        assert not isinstance(classes.make_status("x", "0"), classes._NoStatus)
