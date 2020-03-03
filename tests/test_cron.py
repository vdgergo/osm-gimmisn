#!/usr/bin/env python3
#
# Copyright (c) 2020 Miklos Vajna and contributors.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The test_cron module covers the cron module."""

from typing import BinaryIO
from typing import Optional
import io
import os
import unittest
import unittest.mock

import areas
import cron
import util


def get_relations() -> areas.Relations:
    """Returns a Relations object that uses the test data and workdir."""
    workdir = os.path.join(os.path.dirname(__file__), "workdir")
    return areas.Relations(workdir)


def get_abspath(path: str) -> str:
    """Mock get_abspath() that uses the test directory."""
    if os.path.isabs(path):
        return path
    return os.path.join(os.path.dirname(__file__), path)


class TestOverpassSleep(unittest.TestCase):
    """Tests overpass_sleep()."""
    def test_no_sleep(self) -> None:
        """Tests the case when no sleep is needed."""
        def mock_overpass_query_need_sleep() -> int:
            return 0
        mock_sleep_called = False

        def mock_sleep(_seconds: float) -> None:
            nonlocal mock_sleep_called
            mock_sleep_called = True
        with unittest.mock.patch('overpass_query.overpass_query_need_sleep', mock_overpass_query_need_sleep):
            with unittest.mock.patch('time.sleep', mock_sleep):
                cron.overpass_sleep()
                self.assertFalse(mock_sleep_called)

    def test_need_sleep(self) -> None:
        """Tests the case when sleep is needed."""
        sleep_for = 42

        def mock_overpass_query_need_sleep() -> int:
            nonlocal sleep_for
            if sleep_for > 0:
                sleep_for = 0
                return 42
            return sleep_for
        captured_seconds = 0.0

        def mock_sleep(seconds: float) -> None:
            nonlocal captured_seconds
            captured_seconds = seconds
        with unittest.mock.patch('overpass_query.overpass_query_need_sleep', mock_overpass_query_need_sleep):
            with unittest.mock.patch('time.sleep', mock_sleep):
                cron.overpass_sleep()
                self.assertEqual(captured_seconds, 42.0)


class TestUpdateOsmStreets(unittest.TestCase):
    """Tests update_osm_streets()."""
    def test_happy(self) -> None:
        """Tests the happy path."""
        mock_overpass_sleep_called = False

        def mock_overpass_sleep() -> None:
            nonlocal mock_overpass_sleep_called
            mock_overpass_sleep_called = True

        result_from_overpass = "@id\tname\n1\tTűzkő utca\n2\tTörökugrató utca\n3\tOSM Name 1\n4\tHamzsabégi út\n"

        def mock_urlopen(_url: str, _data: Optional[bytes] = None) -> BinaryIO:
            buf = io.BytesIO()
            buf.write(result_from_overpass.encode('utf-8'))
            buf.seek(0)
            return buf

        with unittest.mock.patch('util.get_abspath', get_abspath):
            with unittest.mock.patch("cron.overpass_sleep", mock_overpass_sleep):
                with unittest.mock.patch('urllib.request.urlopen', mock_urlopen):
                    relations = get_relations()
                    for relation_name in relations.get_active_names():
                        if relation_name != "gazdagret":
                            relations.get_relation(relation_name).get_config().set_active(False)
                    expected = util.get_content(relations.get_workdir(), "streets-gazdagret.csv")
                    os.unlink(os.path.join(relations.get_workdir(), "streets-gazdagret.csv"))
                    cron.update_osm_streets(relations)
                    self.assertTrue(mock_overpass_sleep_called)
                    actual = util.get_content(relations.get_workdir(), "streets-gazdagret.csv")
                    self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()