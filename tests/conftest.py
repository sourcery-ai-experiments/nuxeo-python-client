# coding: utf-8
from __future__ import print_function, unicode_literals

import logging

import os
import sys

import pytest
from requests.cookies import RequestsCookieJar

from nuxeo.client import Nuxeo
from nuxeo.exceptions import HTTPError

logging.basicConfig(
    format="%(module)-14s %(levelname).1s %(message)s", level=logging.DEBUG
)


@pytest.fixture(scope="function", autouse=True)
def server_log(request, server):
    # To skip that fixture, define *skip_logging* at the top of the test file
    should_log_to_server = getattr(request.module, "skip_logging", False)
    if should_log_to_server:
        return

    msg = ">>> testing: {}.{}".format(
        request.module.__name__, request.function.__name__
    )
    server.operations.execute(command="Log", level="warn", message=msg)


@pytest.fixture(autouse=True)
def no_warnings(recwarn):
    """Fail on warning."""
    yield
    warnings = []
    for warning in recwarn:  # pragma: no cover
        message = str(warning.message)
        if "unclosed" in message:
            # It may be worth fixing tests leaking sockets and file descriptors
            continue
        elif "Python 2.7 will reach" in message:
            # TODO NXPY-129: remove that bloc
            continue
        warn = "{w.filename}:{w.lineno} {w.message}".format(w=warning)
        print(warn, file=sys.stderr)
        warnings.append(warn)
    assert not warnings


@pytest.fixture(scope="module")
def directory(server):
    directory = server.directories.get("nature")
    try:
        directory.delete("foo")
    except HTTPError:
        pass
    return directory


@pytest.fixture(scope="module")
def repository(server):
    return server.documents


@pytest.fixture(scope="session")
def host():
    return os.environ.get("NXDRIVE_TEST_NUXEO_URL", "http://localhost:8080/nuxeo")


@pytest.fixture(scope="module")
def server(host):
    cookies = RequestsCookieJar()
    cookies.set("device", "python-client")
    server = Nuxeo(
        host=host,
        auth=("Administrator", "Administrator"),
        cookies=cookies,
    )
    server.client.set(schemas=["dublincore"])

    # Coverage
    assert repr(server)
    assert str(server)

    return server


@pytest.fixture(scope="function")
def retry_server(server):
    server.client.enable_retry()
    yield server
    server.client.disable_retry()
