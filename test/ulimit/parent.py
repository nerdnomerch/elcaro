#!/usr/bin/env python

import os
import sys
import resource
import subprocess

def setlimits():
    # Set maximum CPU time to 1 second in child process, after fork() but before exec()
    print "Setting resource limit in child (pid %d)" % os.getpid()
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (20, 20))

print "CPU limit of parent (pid %d)" % os.getpid(), resource.getrlimit(resource.RLIMIT_CPU)
p = subprocess.Popen(["./child.py"], preexec_fn=setlimits)
print "CPU limit of parent (pid %d) after startup of child" % os.getpid(), resource.getrlimit(resource.RLIMIT_CPU)
p.wait()
print "CPU limit of parent (pid %d) after child finished executing" % os.getpid(), resource.getrlimit(resource.RLIMIT_CPU)
