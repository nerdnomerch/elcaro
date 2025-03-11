#!/usr/bin/env python

import os
import sys
import resource
import time

print "CPU limit of child (pid %d)" % os.getpid(), resource.getrlimit(resource.RLIMIT_CPU)

print "Start : %s" % time.ctime()
while True:
    pass
print "End : %s" % time.ctime()
