import os
from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from socket import socket

import urllib3


def split_path(path):
    splits = list()
    while path != "/":
        path, split = os.path.split(path)
        splits.append(split)
    return splits[::-1]


class BytesIOSocket(socket):
    def __init__(self, content):
        self.handle = BytesIO(content)

    def makefile(self, mode):
        return self.handle


def response_from_bytes(data) -> urllib3.HTTPResponse:
    sock = BytesIOSocket(data)

    response = HTTPResponse(sock)
    response.begin()

    return urllib3.HTTPResponse.from_httplib(response)


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message=None, explain=None):
        self.error_code = code
        self.error_message = message
