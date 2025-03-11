#!/usr/bin/env python3

import argparse
import datetime
import json
import logging.handlers
import os
import resource
import signal
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import ipfshttpclient

from watcher import Watcher


class Terminator:
    terminated = threading.Event()

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.terminated.set()


class Script:
    def __init__(self, _request, _ipfs):
        self.ipfs = _ipfs
        self.request = None
        self.response = None

        with open(_request) as f:
            self.request = json.load(f)

    @staticmethod
    def setlimits():
        resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
        resource.setrlimit(resource.RLIMIT_NOFILE, (20, 20))

    def _check_script(self, script, errors):
        forbidden_functions = ["exec", "eval"]
        forbidden_sequences = ["__"]
        allowed_sequences = ["__init__", "__del__", "__str__"]

        for seq in allowed_sequences:
            script = script.replace(seq, "")

        ok = True
        for seq in forbidden_sequences:
            if script.find(seq) != -1:
                ok = False

        if ok:
            for seq in forbidden_functions:
                if script.find(seq + "(") != -1:
                    ok = False

        if not ok:
            errors.append("check script: failure: usage of functions " + str(forbidden_functions) + " is forbidden. " +
                          "Also '__' can not be used, except for " + str(allowed_sequences))

        return ok

    def _execute(self, errors):
        response = {}
        script_file = tempfile.NamedTemporaryFile()
        script_content = self.ipfs.cat(self.request["content_hash"], length=1024 * 1024).decode()
        if not self._check_script(script_content, errors):
            return response
        basedir = os.path.dirname(os.path.realpath(__file__))
        with open(basedir + "/exec_prelude.py", 'r') as reader:
            script_file.write(bytes(reader.read(), 'utf-8'))

        arguments = ""
        for index in range(0, len(self.request["argument_types"])):
            arg_type = self.request["argument_types"][index]
            arg_value = self.request["arguments"][index]
            if arg_type == "string":
                arguments += '"' + str(arg_value) + '", '
            else:
                arguments += str(arg_value) + ", "

        script_file.write(bytes(script_content, 'utf-8'))
        read_result = "if __name__ == '__main__':\n" \
                      "    __elcora_result = " + self.request["function_name"] + "(" + arguments + ")\n"

        script_file.write(bytes("\n", 'utf-8'))
        script_file.write(bytes(read_result, 'utf-8'))
        script_file.write(bytes("\n", 'utf-8'))

        with open(basedir + "/exec_epilogue.py", 'r') as reader:
            script_file.write(bytes(reader.read(), 'utf-8'))

        script_file.flush()

        with open(script_file.name, 'r') as reader:
            full_script = reader.read()
            response["full_script"] = self.ipfs.add_bytes(full_script.encode('utf-8'))

        pid = -1
        status = 0
        try:
            logging.info("- executing script " + script_file.name)
            process = subprocess.Popen(["python3", script_file.name],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       close_fds=True,
                                       preexec_fn=Script.setlimits)
            pid = process.pid
            status = process.wait()
            out, err = process.communicate()

            with open(script_file.name + ".result") as f:
                response.update(json.load(f))
                os.remove(script_file.name + ".result")

            logging.info("- result = " + json.dumps(response))

            if status == 0:
                execution_context = \
                    "// elcaro execution log [{}]\n" \
                    "// " + str(self.request['function']) + str(self.request['arguments']) + " -> " + str(
                        response["result"]) + "\n\n"
                out = execution_context.format("stdout") + out.decode('utf-8')
                out = out.replace(script_file.name, "ipfs://" + self.request["content_hash"])
                err = execution_context.format("stderr") + err.decode('utf-8')
                err = err.replace(script_file.name, "ipfs://" + self.request["content_hash"])
                response["stdout"] = self.ipfs.add_bytes(out.encode('utf-8'))
                response["stderr"] = self.ipfs.add_bytes(err.encode('utf-8'))
        except:
            status = -1
        finally:
            response["pid"] = pid
            response["status"] = status

        script_file.close()

        return response

    def execute(self):
        logging.info("- execute " + str(self.request))
        response = {
            "start": datetime.datetime.now().isoformat()
        }
        errors = []
        warnings = []
        try:
            if self.request:
                logging.info("- executing request " + self.request['request_hash'])
                function_url = self.request['function']
                function_url = urlparse(function_url)
                protocol = function_url.scheme
                content_hash = function_url.netloc
                function = function_url.path
                if protocol == 'ipfs':
                    if not (len(function) > 3 and function[0] == "/" and function.count("/") == 1 and
                            function.count("(") == 1 and function.count(")")) == 1 and \
                            function.find("(") < function.find(")"):
                        errors.append("function url: parse error: invalid function url")

                    function_name = function[1:function.find("(")].strip()
                    function_argument_types = function[function.find("(") + 1:function.find(")")].split(",")

                    if not len(self.request['arguments']) == len(function_argument_types):
                        errors.append("function url: argument count does not match with type count")

                    self.request["content_hash"] = content_hash
                    self.request["function_name"] = function_name
                    self.request["argument_types"] = function_argument_types
                else:
                    errors.append("function url: error: only ipfs is supported")
            else:
                errors.append("request json invalid")

            if len(errors) == 0:
                response.update(self._execute(errors))
        finally:
            response["end"] = datetime.datetime.now().isoformat()
            if len(errors) > 0:
                response["errors"] = errors
                response["status"] = -1

            if len(warnings) > 0:
                response["warnings"] = warnings

        self.response = response
        return self.request, self.response


class Executor:
    def __init__(self, _config, _queue):
        self.config = _config
        self.queue = _queue
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.terminate = threading.Event()
        self.ipfs = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
        self.thread = threading.Thread(target=self.importer,
                                       args=(),
                                       daemon=True)
        self.thread.start()

    def __del__(self):
        self.terminate.set()
        self.thread.join()

    def importer(self):
        while not self.terminate.isSet():
            while not self.queue.empty():
                request = self.queue.get(True)
                self.executor.submit(self.exec, request)
            time.sleep(1)

    def exec(self, _request):
        request, response = Script(_request, self.ipfs).execute()
        result = request
        result["response"] = response
        os.remove(_request)
        index = ""
        if 'index' in result:
            index = "@" + result['index']
        with open(self.config.response +
                  "/" + result['request_hash'] + index + ".json", "w") as outfile:
            outfile.write(json.dumps(result, indent=4))
        logging.info(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='elcaro oracle executor')
    parser.add_argument('--log', help='path to executor logfile', default='/data/executor/executor.log')
    parser.add_argument('--request', help='path to executor request directory',
                        default='/data/executor/request')
    parser.add_argument('--response', help='path to executor response directory',
                        default='/data/executor/response')
    config = parser.parse_args()
    handler = logging.handlers.WatchedFileHandler(config.log)
    root = logging.getLogger()
    root.setLevel(os.environ.get('LOGLEVEL', 'INFO'))
    root.addHandler(handler)

    logging.info('elcaro oracle executor started')

    ipfs = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')

    terminator = Terminator()

    watcher = Watcher(config.request)
    executor = Executor(config, watcher.queue)
    while not terminator.terminated.isSet():
        time.sleep(1)
    del executor

    logging.info('shutting down elcaro oracle executor...')
