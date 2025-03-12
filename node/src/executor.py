#!/usr/bin/env python3

import time
import json
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import ipfshttpclient
from concurrent.futures import ThreadPoolExecutor
from time import sleep

executor = None


def task(ipfs_cid):
    client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
    return client.cat(ipfs_cid)


def on_created(event):
    print(f"hey, {event.src_path} has been created!")


def on_deleted(event):
    print(f"what the f**k! Someone deleted {event.src_path}!")


def on_modified(event):
    print(f"hey buddy, {event.src_path} has been modified")


def on_moved(event):
    print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")


if __name__ == "__main__":
    executor = ThreadPoolExecutor(5)
    future = executor.submit(task, ("QmZrPf6xunDiwsdbPS33oxiPQoTeztmP6KkWfFPjBjdWH7"))
    print(future.done())
    sleep(2)
    print(future.done())
    print(future.result())

    j = json.loads('{"one" : "1", "two" : "2", "three" : "3"}')
    print(j)
    print(j["one"])

    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler.on_created = on_created
    my_event_handler.on_deleted = on_deleted
    my_event_handler.on_modified = on_modified
    my_event_handler.on_moved = on_moved
    path = "/tmp/"
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=False)
    my_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()

    print("down")
