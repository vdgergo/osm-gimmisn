#!/usr/bin/env python3
#
# Copyright 2019 Miklos Vajna. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#

"""The overpass_query module allows getting data out of the OSM DB without a full download."""

from typing import cast
import urllib.request
import urllib.error
import re
import sys


def overpass_query(query: str) -> str:
    """Posts the query string to the overpass API and returns the result string."""
    # Import only inside the function, as util imports a function from this module.
    # pylint: disable=import-outside-toplevel
    import util
    url = util.Config.get_overpass_uri() + "/api/interpreter"

    sock = urllib.request.urlopen(url, bytes(query, "utf-8"))
    buf = sock.read()
    sock.close()

    return cast(str, buf.decode('utf-8'))


def overpass_query_need_sleep() -> int:
    """Checks if we need to sleep before executing an overpass query."""
    # Import only inside the function, as util imports a function from this module.
    # pylint: disable=import-outside-toplevel
    import util
    try:
        with urllib.request.urlopen(util.Config.get_overpass_uri() + "/api/status") as sock:
            buf = sock.read()
    except urllib.error.HTTPError:
        return 0
    status = buf.decode('utf-8')
    sleep = 0
    available = False
    for line in status.splitlines():
        if line.startswith("Slot available after:"):
            # Wait one more second just to be safe.
            sleep = int(re.sub(r".*in (-?\d+) seconds.*", r"\1", line.strip())) + 1
            if sleep <= 0:
                sleep = 1
            break
        if "available now" in line:
            available = True
    if available:
        return 0
    return sleep


def main() -> None:
    """Commandline interface to this module."""
    sock = open(sys.argv[1])
    query = sock.read()
    sock.close()

    try:
        buf = overpass_query(query)

        sys.stdout.write(buf)
    except urllib.error.HTTPError as http_error:
        print("overpass query failed: " + str(http_error))


if __name__ == "__main__":
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
