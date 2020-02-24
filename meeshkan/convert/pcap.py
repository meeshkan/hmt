"""Code for converting pcap to HttpExchange JSON format."""

from sys import argv
from typing import List, Optional, Any, Iterator
from http_types.utils import RequestBuilder, ResponseBuilder
from typing import Iterator
from pathlib import Path
import csv
import json
import shutil
from typing import List, Optional, Dict, Union
from http_types import Request, Response, HttpExchange
import re
import subprocess
from ..logger import get as getLogger

LOGGER = getLogger(__name__)
TSHARK_EXECUTABLE = 'tshark'


def _request_from_tshark(obj) -> Request:
    method = obj["http.request.method"].lower()
    uri = obj['http.request.uri']
    req_line = obj['http.request.line']
    headers = _parse_headers(header_line=req_line)
    body = obj['http.file_data']
    protocol = obj['_ws.col.Protocol'].lower()
    # TODO Parse
    # query = parse_query(obj['http.request.uri.query'])
    query = {}
    # TODO Handle path correctly
    path = uri
    pathname = path
    # TODO
    
    host = headers['x-forwarded-host'] if 'x-forwarded-host' in headers else ''

    if isinstance(host, list):
        raise AssertionError("Did not expect to get list as x-forwarded-host")

    return RequestBuilder.from_dict(dict(
        body=body,
        protocol=protocol,
        method=method,
        headers=headers,
        query=query,
        path=path,
        pathname=pathname,
        host=host,
        bodyAsJson=None))


def _response_from_tshark(obj) -> Response:
    status_code = int(obj['http.response.code'])
    res_line = obj['http.response.line']
    body = obj['http.file_data']  # type: str
    headers = _parse_headers(header_line=res_line)
    return ResponseBuilder.from_dict(dict(bodyAsJson=None, statusCode=status_code, body=body, headers=headers))


def _parse_headers(header_line: str) -> Dict[str, Union[str, List[str]]]:
    # Depends on \\r\\n being a line-break, also removes "\\" from the start of every header
    lines = [cleaned
             for line in header_line.split("\\r\\n")
             for cleaned in (re.sub(r"^\\", "", line),)]

    def line_to_tuple(l: str):
        # dec = l.decode('string_escape')
        if len(l) == 0:
            return None
        split = l.split(":", 1)
        return split[0].strip().lower(), split[1].strip()

    return dict(tupl
                for line in lines
                for tupl in (line_to_tuple(line),)
                if tupl is not None)


# from .meeshkan_types import Request, Response, HttpExchange


def _request_response_parser():
    """Create a parser for parsing tshark objects into HttpExchange.

    Raises:
        Exception: [description]

    Returns:
        [type] -- [description]
    """
    requests = {}

    def parse_request_response_if_res(obj: Any) -> Optional[HttpExchange]:
        """
        Handle one line of tshark dictionary.

        If request, store request to internal dictionary.
        If response, return request-response pair.
        """
        stream_id = obj["tcp.stream"]
        req_method = obj["http.request.method"]

        is_request = True if req_method != "" else False

        if is_request:
            requests[stream_id] = obj
            return None

        # Request corresponding to this response
        request = requests.pop(stream_id)
        response = obj
        req = _request_from_tshark(request)
        res = _response_from_tshark(response)
        req_res = HttpExchange(request=req, response=res)
        return req_res

    return parse_request_response_if_res


def transform_tshark(tshark_csv: Iterator[str]) -> Iterator[HttpExchange]:
    """Convert tshark-produced CSV to an iterator of HttpExchanges.
    
    Arguments:
        tshark_csv {Iterator[str]} -- Lines of CSV produced by tshark.
    
    Returns:
        Iterator[HttpExchange] -- [description]
    """
    parse_request_response = _request_response_parser()
    return (req_res
            for obj in csv.DictReader(tshark_csv, quotechar='\'')
            for req_res in (parse_request_response(obj),)
            if req_res is not None)


def check_tshark_exists():
    if shutil.which(TSHARK_EXECUTABLE) is None:
        raise Exception(
            "Could not find executable {} in PATH.".format(TSHARK_EXECUTABLE))


def convert_pcap(filepath: str) -> Iterator[HttpExchange]:

    check_tshark_exists()

    if filepath == '-':
        raise NotImplementedError("File path '-' detected. Reading from stdin is not implemented yet.")

    resolved_path = Path(filepath).resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError("Not a file: {}".format(filepath))

    tshark_cmd = "tshark -r {} -Y http -E separator=, -E aggregator='\t' -E header=y -E occurrence=a -E quote=s -T fields -e tcp.stream -e _ws.col.Protocol -e http.request.method -e http.request.uri -e http.request.uri.path -e http.request.uri.query -e http.request.full_uri -e http.request.line -e http.transfer_encoding -e http.response.code -e http.response_for.uri -e http.response.line -e http.file_data".format(
        resolved_path)

    # TODO Stream stdout with subprocess.Popen instead of reading the whole output into memory
    tshark_proc = subprocess.run(
        tshark_cmd, shell=True, stdout=subprocess.PIPE)

    if tshark_proc.returncode != 0:
        raise Exception("tshark exited with code {}".format(
            tshark_proc.returncode))

    stdout = tshark_proc.stdout.decode()

    return transform_tshark(iter(stdout.splitlines()))


if __name__ == '__main__':
    filename = argv[1]

    out = convert_pcap(filename)

    for o in out:
        print(json.dumps(o))
