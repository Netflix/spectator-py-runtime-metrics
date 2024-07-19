import gc
import logging
import multiprocessing as mp
import os
import resource
import threading
import time
from sys import platform
from typing import Dict

from spectator.meter.gauge import Gauge
from spectator.registry import Registry


class StatsCollector:
    def __init__(self, registry: Registry):
        self._registry = registry
        self._logger = logging.getLogger("runmetrics.StatsCollector")
        self._enabled = True
        self._period = 30

        # file descriptor metrics
        self._fd_allocated = self._registry.gauge("py.fd", {"id": "allocated"})
        self._fd_max = self._registry.gauge("py.fd", {"id": "max"})

        # garbage collector metrics
        self._gc_enabled = self._registry.gauge("py.gc.enabled")

        self._gc_gen: Dict[int, Dict[str, Gauge]] = {}
        for i in range(0, 3):
            self._gc_gen[i] = {}
            self._gc_gen[i]["collections"] = self._registry.gauge("py.gc.collections", {"gen": f"{i}"})
            self._gc_gen[i]["collected"] = self._registry.gauge("py.gc.collected", {"gen": f"{i}"})
            self._gc_gen[i]["uncollectable"] = self._registry.gauge("py.gc.uncollectable", {"gen": f"{i}"})
            self._gc_gen[i]["threshold"] = self._registry.gauge("py.gc.threshold", {"gen": f"{i}"})
            self._gc_gen[i]["count"] = self._registry.gauge("py.gc.count", {"gen": f"{i}"})

        # multiprocessing metrics
        self._mp_active_children = self._registry.gauge("py.mp.activeChildren")
        self._mp_cpu = self._registry.gauge("py.mp.cpu")

        # resource usage metrics
        self._ru_utime = self._registry.gauge("py.resource.time", {"mode": "user"})
        self._ru_stime = self._registry.gauge("py.resource.time", {"mode": "system"})
        self._ru_maxrss = self._registry.gauge("py.resource.maxResidentSetSize")
        self._ru_minflt = self._registry.gauge("py.resource.pageFaults", {"io.required": "false"})
        self._ru_majflt = self._registry.gauge("py.resource.pageFaults", {"io.required": "true"})
        self._ru_inblock = self._registry.gauge("py.resource.blockOperations", {"id": "input"})
        self._ru_oublock = self._registry.gauge("py.resource.blockOperations", {"id": "output"})
        self._ru_nvcsw = self._registry.gauge("py.resource.contextSwitches", {"id": "voluntary"})
        self._ru_nivcsw = self._registry.gauge("py.resource.contextSwitches", {"id": "involuntary"})

        # threading metrics
        self._threading_active = self._registry.gauge("py.threading.active", {"pid": f"{os.getpid()}"})

    def _target(self):
        self._logger.info("start collecting runtime metrics every %s seconds", self._period)
        while self._enabled:
            self._logger.debug("collect runtime metrics")
            self.collect_stats()
            time.sleep(self._period)
        self._logger.info("stop collecting runtime metrics")

    def collect_stats(self):
        self._collect_fd_stats()
        self._collect_gc_stats()
        self._collect_mp_stats()
        self._collect_resource_stats()
        self._collect_threading_stats()

    def _collect_fd_stats(self):
        self._fd_max.set(resource.RLIMIT_NOFILE)
        if platform == "linux":
            self._fd_allocated.set(len(os.listdir("/proc/self/fd")))

    def _collect_gc_stats(self):
        self._gc_enabled.set(gc.isenabled())

        stats = gc.get_stats()
        threshold = gc.get_threshold()
        count = gc.get_count()

        for i in range(0, 3):
            self._gc_gen[i]["collections"].set(stats[i]["collections"])
            self._gc_gen[i]["collected"].set(stats[i]["collected"])
            self._gc_gen[i]["uncollectable"].set(stats[i]["uncollectable"])
            self._gc_gen[i]["threshold"].set(threshold[i])
            self._gc_gen[i]["count"].set(count[i])

    def _collect_mp_stats(self):
        self._mp_active_children.set(len(mp.active_children()))
        self._mp_cpu.set(mp.cpu_count())

    def _collect_resource_stats(self):
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        self._ru_utime.set(rusage.ru_utime)
        self._ru_stime.set(rusage.ru_stime)
        self._ru_maxrss.set(rusage.ru_maxrss)
        self._ru_minflt.set(rusage.ru_minflt)
        self._ru_majflt.set(rusage.ru_majflt)
        self._ru_inblock.set(rusage.ru_inblock)
        self._ru_oublock.set(rusage.ru_oublock)
        self._ru_nvcsw.set(rusage.ru_nvcsw)
        self._ru_nivcsw.set(rusage.ru_nivcsw)

    def _collect_threading_stats(self):
        self._threading_active.set(threading.active_count())

    def start(self):
        t = threading.Thread(target=self._target, daemon=True)
        t.start()

    def stop(self):
        self._enabled = False
