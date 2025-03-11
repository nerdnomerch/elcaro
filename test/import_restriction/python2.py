#!/usr/bin/env python

import os
import sys
import resource
import time

import importlib

def prevent_imports(name, globals=None, locals=None, fromlist=(), level=0):
    raise ImportError("module '%s' is restricted."%name)

__builtins__.__dict__['__import__'] = prevent_imports

print(dir(__builtins__))

import time
