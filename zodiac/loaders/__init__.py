import re
import logging
import pathlib
import textwrap
import urllib
import socket
import ssl
import enum

import mistune
from PySide2 import QtCore


class FileLoader:
    SCHEME = "file"

    def __init__(self, url):
        self._url = url

    @property
    def content(self):
        _, netloc, path, _, _, _ = urllib.parse.urlparse(self._url)
        filepath = pathlib.Path(netloc, path)
        try:
            with open(filepath) as fh:
                content = fh.read()
        except FileNotFoundError:
            content = textwrap.dedent(
                f"""
                # Error

                Could not find file:

                ```
                    {filepath}
                ```
            """
            )

        return "", content


class GeminiStatus(enum.Enum):
    INPUT = 1
    SUCCESS = 2
    REDIRECT = 3
    TEMPORARY_FAILURE = 4
    PERMANENT_FAILURE = 5
    CLIENT_CERTIFICATE_REQUIRED = 6

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(int(value[0]))
        return super()._missing_(value)


class GeminiLoader:
    SCHEME = "gemini"
    DEFAULT_PORT = 1965
    CRLF = "\r\n"

    MAX_REDIRECTS = 5

    def __init__(self, url):
        self._url = url

    def _decode_header(self, header):
        status, meta = re.match(
            "^(?P<status>\d+)\s+(?P<meta>.*)$", header.decode()
        ).groups()
        return GeminiStatus(status), meta

    def _recv_all(self, ssock):
        data = b""
        while True:
            _d = ssock.recv()
            if _d:
                data += _d
            else:
                break

        return data

    @property
    def content(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        redirect_count = 0
        url = self._url

        while True:
            if redirect_count > self.MAX_REDIRECTS:
                break

            url_info = urllib.parse.urlparse(self._url)
            hostname = url_info.hostname
            port = url_info.port or self.DEFAULT_PORT

            with socket.create_connection((hostname, port)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    ssock.send((url + self.CRLF).encode())
                    data = self._recv_all(ssock)
                    header, *body = data.splitlines()
                    status, meta = self._decode_header(header)

                    if status == GeminiStatus.REDIRECT:
                        url = meta
                        redirect_count += 1
                        continue
                    else:
                        break

        return meta, b"\n".join(body).decode()


SCHEME_MAP = {
    FileLoader.SCHEME: FileLoader,
    GeminiLoader.SCHEME: GeminiLoader,
}


class PageLoader(QtCore.QObject):

    content = QtCore.Signal(str)
    status_msg = QtCore.Signal(str)

    _current_url = ""

    @QtCore.Slot(str)
    def set_url(self, url, *args, **kwargs):
        self._current_url = url

    @QtCore.Slot()
    def load_url(self, *args, **kwargs):
        self.status_msg.emit(f"Loading {self._current_url}")
        loader = self._get_loader(self._current_url)
        mimetype, content = loader.content

        if mimetype == "text/gemini":
            html = mistune.markdown(content)
        else:
            html = mistune.markdown(content)

        self.content.emit(html)
        self.status_msg.emit(f"Loaded {self._current_url}")

    def _get_loader(self, url):
        scheme, netloc, path, paramgs, query, fragment = urllib.parse.urlparse(url)
        return SCHEME_MAP[scheme](url)
