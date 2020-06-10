"""
    isort:skip_file
"""
import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from textwrap import wrap
from urllib import request

import psutil
from pyfiglet import Figlet

from clint.textui import colored, puts
from progress.spinner import MoonSpinner

API_CALLS = """from urllib import request
from http_types import HttpExchange
from http_types.utils import RequestBuilder, ResponseBuilder, HttpExchangeWriter
from io import StringIO

def make_pokemon_request(path):
    req = request.Request('http://localhost:8000%s' % path, headers={
        'user-agent': 'python', 'Host': 'pokeapi.co', 'X-Meeshkan-Scheme': 'https'
    })
    res = request.urlopen(req)
    res.read()

PATHS = [
    '/api/v2/pokemon/1/',
    '/api/v2/pokemon/2/',
    '/api/v2/pokemon/3/',
    '/api/v2/pokemon/4/',
    '/api/v2/pokemon/5/',
    '/api/v2/pokemon/6/',
    '/api/v2/pokemon/7/',
    '/api/v2/pokemon/8/',
    '/api/v2/pokemon/9/',
    '/api/v2/pokemon/10/',
    '/api/v2/pokemon/',
    '/api/v2/type/1/',
    '/api/v2/type/2/',
    '/api/v2/type/3/',
    '/api/v2/type/4/',
    '/api/v2/type/5/',
    '/api/v2/type/6/',
    '/api/v2/type/7/',
    '/api/v2/type/8/',
    '/api/v2/type/9/',
    '/api/v2/type/10/',
    '/api/v2/type/',
    '/api/v2/ability/1/',
    '/api/v2/ability/2/',
    '/api/v2/ability/3/',
    '/api/v2/ability/4/',
    '/api/v2/ability/5/',
    '/api/v2/ability/6/',
    '/api/v2/ability/7/',
    '/api/v2/ability/8/',
    '/api/v2/ability/9/',
    '/api/v2/ability/10/',
    '/api/v2/ability/',
]

for x, path in enumerate(PATHS):
    print("  ** Calling https://pokeapi.co%s, path %d of %d" % (path, x + 1, len(PATHS)))
    make_pokemon_request(path)
"""

MERGE_SPECS = """from openapi_typed_2 import convert_to_openapi, convert_from_openapi
import json
from dataclasses import replace
import os

with open('__hmt__/replay/openapi.json', 'r') as replay_file:
    with open('__hmt__/gen/openapi.json', 'r') as gen_file:
        replay = convert_to_openapi(json.loads(replay_file.read()))
        gen = convert_to_openapi(json.loads(gen_file.read()))
        new = replace(replay, paths = { **replay.paths, **gen.paths })
        try:
            os.mkdir('__hmt__/both')
        except: pass # exists
        with open('__hmt__/both/openapi.json', 'w') as both_file:
            both_file.write(json.dumps(convert_from_openapi(new), indent=2))
"""


async def read_stream(p, server_started):
    try:
        while p.poll() is None:
            line = p.stdout.readline()
            if "Meeshkan is running" in line:
                server_started.set_result(0)
            await asyncio.sleep(0.1)
    finally:
        if not server_started.done():
            server_started.set_result(1)


async def run_bar(message, timeout, sertver_started, interval=0.1):
    bar = MoonSpinner(message)
    spent = 0
    while spent < timeout and not sertver_started.done():
        bar.next()
        await asyncio.sleep(interval)
        spent += interval
    bar.finish()


def building():
    # for now do nothing
    pass


def kill_proc_tree(p):
    if p.poll() is None:
        parent = psutil.Process(p.pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except Exception:
                pass
        psutil.wait_procs(children)
        if p.poll() is None:
            try:
                parent.kill()
            except Exception:
                pass
            parent.wait()


class CLI:
    def __init__(self, loop, use_real_input=True, throw_on_non_zero_exit=False):
        self._loop = loop
        self.use_real_input = use_real_input
        self.throw_on_non_zero_exit = throw_on_non_zero_exit

    def m_print(self, s):
        print("\n".join(wrap(s, width=60)))

    def m_input(self, s):
        text = "\n".join(wrap(s, width=60))
        if self.use_real_input:
            return input(text)
        time.sleep(2)
        return ""

    async def run(self):
        f = Figlet(font="slant")
        print(f.renderText("hmt"))
        puts(colored.cyan("The tutorial!!", bold=True))
        self.m_input("Press ENTER to continue...")
        ############################
        self.m_print("")
        self.m_print("##############################")
        self.m_print("")
        self.m_print(
            "Meeshkan allows you to create mocks of APIs from server traffic and OpenAPI specs.  To start, we'll record some server traffic.  But before we get started, there are a few things you should know."
        )
        self.m_print("")
        self.m_print(
            "First, Meeshkan will create a directory called __hmt__ in the current working directory.  Don't put anything special in there, as it may get overwritten by this tutorial!"
        )
        self.m_print("")
        self.m_print(
            "Next, this tutorial makes some network calls to the Pokemon API (pokeapi.co).  Please make sure you have a working internet connection."
        )
        self.m_print("")
        i = self.m_input(
            "With that in mind, press ENTER to continue (or the q key followed by ENTER to quit): "
        )
        if i == "q":
            self.m_print("If you change your mind, come back anytime.  Goodbye!")
            sys.exit(0)
        self.m_print("")
        self.m_print("##############################")
        self.m_print("")
        self.m_print(
            "Let's"
            " record a bit of server traffic.  We've written a file to `__hmt__/api_calls.py` to make our recordings.  Meeshkan expects recordings to be in the http-types format (github.com/hmt/http-types), so we'll use that."
        )
        self.m_print("")
        self.m_print(
            "Open up `__hmt__/api_calls.py`.  You'll see that we call the API 33 times using Meeshkan as a forward proxy."
        )
        self.m_print("")
        if os.path.exists("__hmt__"):
            shutil.rmtree("__hmt__")
        os.mkdir("__hmt__")

        with open("__hmt__/api_calls.py", "w") as fi:
            fi.write(API_CALLS)
        self.m_input(
            "After you've checked out `__hmt__/api_calls.py`, press ENTER to launch the proxy and execute the script!"
        )

        with subprocess.Popen(
            "hmt record -r -l __hmt__".split(" "),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=os.getcwd(),
            encoding="utf-8",
        ) as p:
            try:
                await self._server_starting("Starting proxy", p)

                self.m_print("")
                self.m_print("##############################")
                self.m_print("")
                res = subprocess.call("python __hmt__/api_calls.py", shell=True)
                if self.throw_on_non_zero_exit and (res != 0):
                    raise ValueError("Test failed at `python __hmt__/api_calls.py`")
                self.m_print("")
                self.m_input(
                    "Now, if you check out `__hmt__/pokeapi.co.jsonl`, you'll see all of the recorded server traffic. Press ENTER to continue."
                )
                self.m_print("")
                self.m_print("##############################")
                self.m_print("")
                self.m_input(
                    "The command `hmt build` transforms your recordings into an OpenAPI spec.  The `replay` flag tells Meeshkan to build a spec that's identical to the recorded traffic. Press ENTER to invoke `hmt build` in `replay` mode."
                )
                self.m_print("")
                self.m_print("##############################")
                self.m_print("")
                command = "hmt build -i __hmt__/pokeapi.co-recordings.jsonl -o __hmt__/replay -m replay"
                print("$ {}".format(command))
                self.m_print("")
                res = subprocess.call(
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=os.getcwd(),
                )
                if self.throw_on_non_zero_exit and (res != 0):
                    raise ValueError(f"Test failed at `{command}`")
                building()
                self.m_print("")
                self.m_print(
                    "Done.  Now, open up __hmt__/replay/openapi.json. Search within this document for `/api/v2/pokemon/10/:`.  This is a translation of the `GET` request you got from the Pokemon API into OpenAPI."
                )
                self.m_print("")
                self.m_input(
                    "Let's use this spec to create a server that serves back our recordings.  Press ENTER to boot up the mock server."
                )
                self.m_print("")
            finally:
                kill_proc_tree(p)

        with subprocess.Popen(
            "hmt mock __hmt__/replay -r".split(" "),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=os.getcwd(),
            encoding="utf-8",
        ) as p:
            try:
                await self._server_starting("Starting server", p)
                self.m_print("")
                self.m_print("##############################")
                self.m_print("")
                self.m_input(
                    "The server is up and running.  Press ENTER to send a `GET` request to the endpoint `/api/v2/pokemon/10/`."
                )
                req = request.Request(
                    "http://localhost:8000/api/v2/pokemon/10/",
                    headers={"Host": "pokeapi.co", "X-Meeshkan-Scheme": "https"},
                )
                res = request.urlopen(req)
                body = res.read()
                self.m_print("")
                self.m_print("##############################")
                self.m_print("")
                self.m_print("Here is the response we got back from the server.")
                self.m_print("")
                # vanilla print as thre should not be any line wraps
                # may put in function later
                print(
                    json.dumps(
                        json.loads(
                            body
                            if isinstance(body, str)
                            else body.decode("utf8")
                            if isinstance(body, bytes)
                            else ""
                        ),
                        indent=2,
                    )
                )
                self.m_print("..............................")
                self.m_print(
                    "It's the exact same response we got back from the Pokemon API.  Pretty cool, huh?"
                )
                self.m_print("")
                self.m_print(
                    "You can try the same thing.  From curl, Postman or your web browser, try calling endpoints like http://localhost:8000/api/v2/ability/ or http://localhost:8000/api/v2/type/2/.  When doing so, make sure to set the following headers:"
                )
                self.m_print("")
                print(
                    """{
    "Host": "pokeapi.co",
    "X-Meeshkan-Scheme": "https"
}"""
                )
                self.m_print("")
                self.m_input(
                    "Once you're done exploring, press ENTER to turn off the server and continue."
                )
                self.m_print("")
            finally:
                kill_proc_tree(p)

        self.m_print("")
        self.m_print("##############################")
        self.m_print("")
        self.m_print(
            "Now, let's build a new spec.  This time, instead of serving back fixed data, we will use the recordings to create _synthetic_ data.   We do this by invoking `hmt build --mode gen`."
        )
        self.m_print("")
        self.m_input("Press ENTER to build the new spec.")
        self.m_print("")
        self.m_print("Hang tight, we're building your spec!")
        self.m_print("")
        command = (
            "hmt build -i __hmt__/pokeapi.co-recordings.jsonl -o __hmt__/gen -m gen"
        )
        print("$ {}".format(command))
        self.m_print("")
        res = subprocess.call(
            command,
            shell=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            cwd=os.getcwd(),
        )
        if self.throw_on_non_zero_exit and (res != 0):
            raise ValueError(f"Test failed at `{command}`")
        self.m_print("")
        building()
        self.m_print("")
        self.m_print("Done.  In __hmt__/gen/, you'll see a new OpenAPI spec.")
        self.m_print("")
        self.m_input(
            "Let's use this spec to create some _synthetic_ data.  Press ENTER to reboot the mock server on port 8000."
        )
        self.m_print("")
        with subprocess.Popen(
            "hmt mock __hmt__/gen -r".split(" "),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=os.getcwd(),
            encoding="utf-8",
        ) as p:
            try:
                self.m_print("##############################")
                self.m_print("")
                await self._server_starting("Starting server", p)
                self.m_print("")
                self.m_input(
                    "The server is up and running.  Press ENTER to send a `GET` request to the endpoint `/api/v2/pokemon/10/`."
                )
                req = request.Request(
                    "http://localhost:8000/api/v2/pokemon/10/",
                    headers={"Host": "pokeapi.co", "X-Meeshkan-Scheme": "https"},
                )
                res = request.urlopen(req)
                body = res.read()
                self.m_print("")
                self.m_print("##############################")
                self.m_print("")
                self.m_print("Here is the response we got back from the server.")
                self.m_print("")
                # vanilla print as thre should not be any line wraps
                # may put in function later
                print(
                    json.dumps(
                        json.loads(
                            body
                            if isinstance(body, str)
                            else body.decode("utf8")
                            if isinstance(body, bytes)
                            else ""
                        ),
                        indent=2,
                    )
                )
                self.m_print("..............................")
                self.m_print("")
                self.m_print(
                    "The data above is synthetic, but it has the same layout as the recorded data."
                )
                self.m_print("")
                self.m_print(
                    "Why synthetic data?  Well, I'm glad you asked!  Two main reasons."
                )
                self.m_print("")
                self.m_print(
                    "1. Security breaches are most common when dealing with log files and in test environments.  So, when testing, you never want to use real data if possible."
                )
                self.m_print(
                    "2. Using synthetic data forces you write tests that focus on business logic rather than focusing on the content of fixtures, which is (in our opinion) a cleaner way to do testing."
                )
                self.m_print("")
                self.m_print(
                    "From curl, postman or your web browser, try calling http://localhost:8000/api/v2/pokemon/{id}/ , where `{id}` is _any_ positive integer. And when doing so, make sure to set following two headers:"
                )
                self.m_print("")
                print(
                    """{
    "Host": "pokeapi.co",
    "X-Meeshkan-Scheme": "https"
}"""
                )
                self.m_print("")
                self.m_input(
                    "You'll see that Meeshkan generates a synthetic response for an arbitrary Pokemon. Once you're done exploring, press ENTER to turn off the server and continue."
                )
                self.m_print("")
            finally:
                kill_proc_tree(p)

        self.m_print("")
        self.m_print("##############################")
        self.m_print("")
        with open("__hmt__/merge_specs.py", "w") as fi:
            fi.write(MERGE_SPECS)
        self.m_input(
            "Finally, open the file `merge_specs.py` that we created in the __hmt__ directory.  It's a script that merges together the two OpenAPI specs - replay and gen - created by Meeshkan.  After you've looked at it, press ENTER to execute it."
        )
        self.m_print("")
        self.m_print("$ python __hmt__/merge_specs.py")
        self.m_print("")
        res = subprocess.call("python __hmt__/merge_specs.py", shell=True)
        if self.throw_on_non_zero_exit and (res != 0):
            raise ValueError("Test failed at `python __hmt__/merge_specs.p`")
        self.m_print(
            "Done.  In `__hmt__/both/`, you'll see an OpenAPI spec that combines _both_ the fixtures from `__hmt__/replay/openapi.json` and the synthetic spec from `__hmt__/replay/openapi.json`."
        )
        self.m_print("")
        self.m_input(
            "Like the other two specs, this one can be used to create a mock server.  Try it yourself!  After this tutorial, run `hmt mock -i __hmt__/both -r`, making sure to set the same headers as before, and see how the server responds.  Press ENTER to continue."
        )
        self.m_print("")
        self.m_print("##############################")
        self.m_print("")
        self.m_print(
            "Thanks for checking out Meeshkan!  There are several other cool features, like callbacks to implement stateful logic and various connectors from libraries and platforms like Express and Kong."
        )
        self.m_print("")
        self.m_print(
            "If you have a moment, please fill out our post-tutorial survey on https://hmt.typeform.com/to/FpRakX.  Besides helping us improve Meeshkan, it will help us improve this and other tutorials."
        )
        self.m_print("")
        self.m_print("Take care and happy mocking!")

    async def _server_starting(self, message, p, timeout=10):
        server_started = self._loop.create_future()
        self._loop.create_task(read_stream(p, server_started))
        self._loop.create_task(run_bar(message, timeout, server_started))
        try:
            await asyncio.wait_for(server_started, timeout=timeout)
            if server_started.result() != 0:
                raise Exception(
                    "Unable to start Meeshkan. Please, check logs at ~/.hmt/logs for details."
                )
        except asyncio.TimeoutError:
            raise Exception(
                "Unable to start Meeshkan in 10 seconds. Please, check logs at ~/.hmt/logs for details."
            )


def run_tutorial():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(CLI(loop).run())
