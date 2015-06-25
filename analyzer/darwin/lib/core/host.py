#!/usr/bin/env python
# Copyright (C) 2015 Dmitry Rodionov
# This file is part of my GSoC'15 project for Cuckoo Sandbox:
#	http://www.cuckoosandbox.org
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.

import socket
from time import sleep
from bson import BSON

class CuckooHost:

    sockets = {}

    def __init__(self, host_ip, host_port):
        self.ip = host_ip
        self.port = host_port

    def send_api(self, thing):
        """  """
        pid = thing.pid
        if not self.sockets.has_key(pid):
            self.sockets[pid] = self._socket_for_pid(pid)
        s = self.sockets[pid]

        if not s:
            raise Exception("CuckooHost error: could not create socket.")

        # FIXME(rodionovd): remember which APIs we've described earlier
        lookup_idx = 42
        self._send_api_description(lookup_idx, thing)

        # Here's an api object:
        # {
        #     "I"    : (int)<index in the API lookup table>,
        #     "T"    : (int)<caller thread id>,
        #     "t"    : (int)<time since a process launch>,
        #     "args" : [
        #         (int)<1 if this API call was successfull, 0 otherwise>,
        #         (int)<return value>,
        #         (any)<value the first argument>,
        #         (any)<value the second argument>,
        #                       ...
        #         (any)<value the n-th argument>,
        #     ]
        # }
        s.sendall(BSON.encode({
            "I"    : lookup_idx,
            "T"    : thing.tid,
            "t"    : 0,   # FIXME(rodionovd): put an actual value here
            "args" : self._prepare_args(thing)
        }))

    def _socket_for_pid(self, pid):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip, self.port))
        s.sendall("BSON\n")
        self._send_new_process(s, pid)
        return s

    def _send_api_description(self, lookup_idx, thing):
        # Here's an api description object:
        # {
        #     "I"        : (string)<index in the API lookup table>,
        #     "name"     : (string)<API name>,
        #     "type"     : "info",
        #     "category" : (string)<an API category (e.g. "memory" or "network")>
        #     "args"     : [
        #         "is_success",
        #         "retval",
        #         (string)<description of the first argument>,
        #         (string)<description of the second argument>,
        #                       ...
        #         (string)<description of the n-th argument>,
        #     ]
        # }
        self.sockets[thing.pid].sendall(BSON.encode({
            "I"        : lookup_idx,
            "name"     : thing.api,
            "type"     : "info",
            "category" : "unknown", # FIXME(rodionovd): put an actual value here
            "args"     : self._args_description(thing)
        }))

    def _prepare_args(self, thing):
        result = [
            1,  # FIXME(rodionovd): put an actual value here
            thing.retval
        ]
        for arg in thing.args: result.append(arg)
        return result

    def _args_description(self, thing):
        """ """
        description = ["is_success", "retval"]
        for arg_idx in range(0, len(thing.args)):
            description += ["arg%d" % arg_idx]
        return description

    def _send_new_process(self, socket, pid):
        """  """
        socket.sendall(BSON.encode({
            "I"        : 0,
            "name"     : "__process__",
            "type"     : "info",
            "category" : "unknown",
            "args"     : [
                "is_success",
                "retval",
                "TimeLow", "TimeHigh",
                "ProcessIdentifier", "ParentProcessIdentifier",
                "ModulePath"
            ]
        }))
        socket.sendall(BSON.encode({
            "I"    : 0,
            "T"    : 0,
            "t"    : 0,
            "args" : [
                # FIXME(rodionovd): replace with real values
                1,
                0,
                0, 0,
                pid, 1,
                "dummy"
            ]
        }))
