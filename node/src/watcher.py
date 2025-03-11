from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
import queue
import fnmatch
import os


class Watcher:
    def __init__(self, path):
        self.queue = queue.Queue()
        for request in Watcher.find("*.json", path):
            self.queue.put(request)
        self.event_handler = PatternMatchingEventHandler("*.json", "", False, False)
        self.event_handler.on_created = self.on_created
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path, recursive=False)
        self.observer.start()

    @staticmethod
    def find(pattern, path):
        result = []
        for root, dirs, files in os.walk(path):
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    result.append(os.path.join(root, name))
        return result

    def __del__(self):
        self.observer.stop()
        self.observer.join()

    def on_created(self, event):
        self.queue.put(event.src_path)
