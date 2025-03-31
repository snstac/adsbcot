#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ADSBCOT Class Tests."""

import pytest
from adsbcot.classes import ADSBWorker
from configparser import ConfigParser, SectionProxy
import asyncio
import logging

from unittest.mock import patch, MagicMock


@pytest.fixture
def config():
    config_parser = ConfigParser()
    config_parser.read_dict(
        {
            "DEFAULT": {
                "INCLUDE_TISB": "false",
                "TISB_ONLY": "false",
                "INCLUDE_ALL_CRAFT": "true",
            }
        }
    )
    return config_parser["DEFAULT"]


@pytest.fixture
def real_queue():
    return asyncio.Queue()


@pytest.fixture
def real_worker(real_queue, config):
    return ADSBWorker(real_queue, config)


class MockWriter:
    """Mock CoT Event Writer."""

    def __init__(self):
        self.events = []

    async def send(self, event):
        self.events.append(event)


@pytest.fixture
def mock_writer():
    return MockWriter()


def test_calc_altitude(real_worker):
    craft_with_both_altitudes = {"alt_baro": 37000, "alt_geom": 37500}
    # Test with both altitudes
    result = real_worker.calc_altitude(craft_with_both_altitudes)
    assert result == {}


def test_calc_altitude_no_alt_geom(real_worker):
    craft_with_only_baro = {"alt_baro": 37000}
    craft_with_ground_altitude = {"alt_baro": "ground"}
    craft_with_no_altitude = {}

    # Test with only barometric altitude
    result = real_worker.calc_altitude(craft_with_only_baro)
    assert result == {}

    # Test with ground altitude
    result = real_worker.calc_altitude(craft_with_ground_altitude)
    assert result == {}

    # Test with no altitude
    result = real_worker.calc_altitude(craft_with_no_altitude)
    assert result == {}


def test_calc_altitude_with_cache(real_worker):
    craft_with_both_altitudes = {"alt_baro": 37000, "alt_geom": 37500}
    craft_with_only_baro = {"alt_baro": 37000}

    # Test with both altitudes
    result = real_worker.calc_altitude(craft_with_both_altitudes)
    assert result == {}

    # Test with only barometric altitude
    result = real_worker.calc_altitude(craft_with_only_baro)
    assert result == {"x_alt_baro_offset": 0.0, "x_alt_geom": 37000.0}


@pytest.mark.asyncio
async def test_handle_data_none_data(real_worker, capsys):
    data = None
    result = await real_worker.handle_data(data)
    captured = capsys.readouterr()
    assert result is None
    # assert "Invalid aircraft data, should be a Python list." in captured.err


@pytest.mark.asyncio
async def test_handle_data_invalid_data(real_worker, capsys):
    data = "invalid_data"
    result = await real_worker.handle_data(data)
    captured = capsys.readouterr()
    assert result is None
    # assert "Invalid aircraft data, should be a Python list." in captured.err


@pytest.mark.asyncio
async def test_handle_data_empty_list(real_worker):
    data = []
    result = await real_worker.handle_data(data)
    assert result is None


@pytest.mark.asyncio
def test_ADSBWorker():
    """Tests the ADSBWorker class."""
    config = ConfigParser()
    config.read_dict(
        {
            "DEFAULT": {
                "INCLUDE_TISB": "false",
                "TISB_ONLY": "false",
                "INCLUDE_ALL_CRAFT": "true",
            }
        }
    )
    config = config["DEFAULT"]
    worker = ADSBWorker(asyncio.Queue(), config)
    assert worker.config == config
    # assert worker.known_craft_db == {}
    assert worker.queue.empty()
    assert worker._logger.level == logging.INFO
    assert worker._logger.handlers[0].level == logging.INFO
    assert worker.altitudes == {}


# @pytest.mark.asyncio
# async def test_handle_data_valid_data(real_worker):
#     data = [{"hex": "ABC123"}, {"hex": "DEF456"}]
#     with patch.object(
#         real_worker, "process_craft", return_value="ABC123"
#     ) as mock_process_craft:
#         await real_worker.handle_data(data)
#         assert mock_process_craft.call_count == 2


@pytest.mark.asyncio
async def test_process_craft_invalid_data(real_worker, capsys):
    craft = "invalid_data"
    result = await real_worker.process_craft(craft)
    captured = capsys.readouterr()
    assert result is None
    # assert "Aircraft list item was not a Python `dict`." in captured.err


@pytest.mark.asyncio
async def test_process_craft_no_icao(real_worker, capsys):
    craft = {"some_key": "some_value"}
    result = await real_worker.process_craft(craft)
    captured = capsys.readouterr()
    assert result is None
    # assert "No ICAO in craft data" in captured.err


@pytest.mark.asyncio
async def test_process_craft_exclude_tisb(real_worker):
    craft = {"hex": "~ABC123"}
    real_worker.config["INCLUDE_TISB"] = "false"
    result = await real_worker.process_craft(craft)
    assert result is None


@pytest.mark.asyncio
async def test_process_craft_tisb_only(real_worker):
    craft = {"hex": "ABC123"}
    real_worker.config["TISB_ONLY"] = "true"
    result = await real_worker.process_craft(craft)
    assert result is None


@pytest.mark.asyncio
async def test_process_craft_unknown_craft(real_worker):
    craft = {"hex": "ABC123"}
    real_worker.known_craft_db = {}
    real_worker.config["INCLUDE_ALL_CRAFT"] = "false"
    with patch("aircot.get_known_craft", return_value=None):
        result = await real_worker.process_craft(craft)
        assert result is None


@pytest.mark.asyncio
async def test_process_craft_no_altitude_data(real_worker):
    craft = {"hex": "ABC123"}
    real_worker.known_craft_db = {}
    with patch("aircot.get_known_craft", return_value={"hex": "ABC123"}):
        with patch.object(real_worker, "calc_altitude", return_value={}):
            result = await real_worker.process_craft(craft)
            assert result is None


@pytest.mark.asyncio
async def test_process_craft_empty_cot(real_worker):
    craft = {"hex": "ABC123"}
    real_worker.known_craft_db = {}
    with patch("aircot.get_known_craft", return_value={"hex": "ABC123"}):
        with patch.object(
            real_worker, "calc_altitude", return_value={"alt_baro": 37000}
        ):
            with patch("adsbcot.adsb_to_cot", return_value=None):
                result = await real_worker.process_craft(craft)
                assert result is None


# @pytest.mark.asyncio
# async def test_process_craft_success(real_worker):
#     craft = {"hex": "ABC123"}
#     real_worker.known_craft_db = {}
#     with patch("aircot.get_known_craft", return_value={"hex": "ABC123"}):
#         with patch.object(
#             real_worker, "calc_altitude", return_value={"alt_baro": 37000}
#         ):
#             with patch("adsbxcot.adsbx_to_cot", return_value=b"cot_event"):
#                 with patch.object(real_worker, "put_queue") as mock_put_queue:
#                     result = await real_worker.process_craft(craft)
#                     assert result == "ABC123"
#                     mock_put_queue.assert_called_once_with(b"cot_event")
