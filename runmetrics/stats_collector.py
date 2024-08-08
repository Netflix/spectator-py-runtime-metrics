import gc
import logging
import multiprocessing as mp
import os
import platform
import resource
import sys
import threading
import time
from typing import Dict, Optional

from spectator.meter.gauge import Gauge
from spectator.registry import Registry

try:
    import psutil
except ImportError:
    pass


class StatsCollector:
    def __init__(self, registry: Registry, worker_id: Optional[str] = None, period: int = 30):
        self._registry = registry
        self._logger = logging.getLogger(__name__)
        self._enabled = True
        self._period = period
        self._worker_id = worker_id

        # file descriptor metrics
        self._fd_allocated = self._registry.gauge("py.fd", self._with_worker_id({"id": "allocated"}))
        self._fd_max = self._registry.gauge("py.fd", self._with_worker_id({"id": "max"}))

        # garbage collector metrics
        self._gc_enabled = self._registry.gauge("py.gc.enabled", self._with_worker_id({}))

        self._gc_gen: Dict[int, Dict[str, Gauge]] = {}
        for i in range(0, 3):
            self._gc_gen[i] = {}
            self._gc_gen[i]["collections"] = self._registry.gauge("py.gc.collections", self._with_worker_id({"gen": f"{i}"}))
            self._gc_gen[i]["collected"] = self._registry.gauge("py.gc.collected", self._with_worker_id({"gen": f"{i}"}))
            self._gc_gen[i]["uncollectable"] = self._registry.gauge("py.gc.uncollectable", self._with_worker_id({"gen": f"{i}"}))
            self._gc_gen[i]["threshold"] = self._registry.gauge("py.gc.threshold", self._with_worker_id({"gen": f"{i}"}))
            self._gc_gen[i]["count"] = self._registry.gauge("py.gc.count", self._with_worker_id({"gen": f"{i}"}))

        self._gc_pause = self._registry.timer("py.gc.pause", self._with_worker_id({}))
        self._gc_time_since_last = self._registry.age_gauge("py.gc.timeSinceLast", self._with_worker_id({}))

        if platform.python_implementation() == "CPython":
            gc.callbacks.append(self._gc_callback)

        # multiprocessing and os metrics
        self._mp_active_children = self._registry.gauge("py.mp.activeChildren", self._with_worker_id({}))
        self._os_cpu = self._registry.gauge("py.os.cpu", self._with_worker_id({}))

        # resource usage metrics
        self._ru_utime = self._registry.gauge("py.resource.time", self._with_worker_id({"mode": "user"}))
        self._ru_stime = self._registry.gauge("py.resource.time", self._with_worker_id({"mode": "system"}))
        self._ru_maxrss = self._registry.gauge("py.resource.maxResidentSetSize", self._with_worker_id({}))
        self._ru_minflt = self._registry.gauge("py.resource.pageFaults", self._with_worker_id({"io.required": "false"}))
        self._ru_majflt = self._registry.gauge("py.resource.pageFaults", self._with_worker_id({"io.required": "true"}))
        self._ru_inblock = self._registry.gauge("py.resource.blockOperations", self._with_worker_id({"id": "input"}))
        self._ru_oublock = self._registry.gauge("py.resource.blockOperations", self._with_worker_id({"id": "output"}))
        self._ru_nvcsw = self._registry.gauge("py.resource.contextSwitches", self._with_worker_id({"id": "voluntary"}))
        self._ru_nivcsw = self._registry.gauge("py.resource.contextSwitches", self._with_worker_id({"id": "involuntary"}))

        # threading metrics
        self._threading_active = self._registry.gauge("py.threading.active", self._with_worker_id({}))

    def _with_worker_id(self, tags: Dict[str, str]) -> Optional[Dict[str, str]]:
        if self._worker_id is not None:
            tags.update({"worker.id": f"{self._worker_id}"})
        if len(tags) == 0:
            return None
        else:
            return tags

    def _gc_callback(self, phase: str, info: Dict[str, int]) -> None:
        if phase == "start":
            self._gc_time_since_last.now()
            self._gc_start = time.monotonic()
        else:
            self._gc_pause.record(time.monotonic() - self._gc_start)

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
        self._collect_mp_os_stats()
        self._collect_resource_stats()
        self._collect_threading_stats()

    def _collect_fd_stats(self):
        self._fd_max.set(resource.RLIMIT_NOFILE)
        if sys.platform == "win32":
            self._fd_allocated.set(psutil.Process().num_handles())
        elif sys.platform == "darwin":
            self._fd_allocated.set(len(os.listdir("/dev/fd")))
        elif sys.platform == "linux":
            self._fd_allocated.set(len(os.listdir("/proc/self/fd")))

    def _collect_gc_stats(self):
        if gc.isenabled():
            self._gc_enabled.set(1)
        else:
            self._gc_enabled.set(0)

        stats = gc.get_stats()
        threshold = gc.get_threshold()
        count = gc.get_count()

        for i in range(0, 3):
            self._gc_gen[i]["collections"].set(stats[i]["collections"])
            self._gc_gen[i]["collected"].set(stats[i]["collected"])
            self._gc_gen[i]["uncollectable"].set(stats[i]["uncollectable"])
            self._gc_gen[i]["threshold"].set(threshold[i])
            self._gc_gen[i]["count"].set(count[i])

    def _collect_mp_os_stats(self):
        self._mp_active_children.set(len(mp.active_children()))
        self._os_cpu.set(os.cpu_count())

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
        self._enabled = True
        t = threading.Thread(target=self._target, daemon=True)
        t.start()

    def stop(self):
        self._enabled = False
