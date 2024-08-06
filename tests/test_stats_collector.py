from collections import namedtuple
from unittest import mock, TestCase

from spectator.config import Config
from spectator.registry import Registry

from runmetrics.stats_collector import StatsCollector


GC_GET_STATS = [
    {'collections': 10, 'collected': 11, 'uncollectable': 12},
    {'collections': 20, 'collected': 21, 'uncollectable': 22},
    {'collections': 30, 'collected': 31, 'uncollectable': 32}
]

Rusage = namedtuple('Rusage', ['ru_utime', 'ru_stime', 'ru_maxrss', 'ru_minflt',
                               'ru_majflt', 'ru_inblock', 'ru_oublock', 'ru_nvcsw', 'ru_nivcsw'])


@mock.patch("resource.RLIMIT_NOFILE", 2)
@mock.patch("sys.platform", "linux")
@mock.patch("gc.get_stats", return_value=GC_GET_STATS)
@mock.patch("gc.get_threshold", return_value=(100, 101, 102))
@mock.patch("gc.get_count", return_value=(200, 201, 202))
@mock.patch("gc.isenabled", return_value=True)
@mock.patch("multiprocessing.active_children", return_value=[])
@mock.patch("os.cpu_count", return_value=4)
@mock.patch("os.getpid", return_value=7)
@mock.patch("os.listdir", return_value=["0"])
@mock.patch("platform.python_implementation", return_value="disable_callback")
@mock.patch("resource.getrusage", return_value=Rusage(1, 2, 3, 4, 5, 6, 7, 8, 9))
@mock.patch("threading.active_count", return_value=5)
class StatsCollectorTest(TestCase):
    def test_collect_stats(self, gc_get_stats, gc_get_threshold, gc_get_count, gc_isenabled,
                           mp_active_children, os_cpu_count, os_getpid, os_listdir,
                           python_impl, resource_getrusage, threading_active_count):
        r = Registry(Config("memory"))
        StatsCollector(r, enable_pid_tag=True).collect_stats()

        messages = r.writer().get()
        self.assertEqual(30, len(messages))

        fd_expected = [
            'g:py.fd,id=max,pid=7:2',
            'g:py.fd,id=allocated,pid=7:1',
        ]
        self.assertEqual(fd_expected, [m for m in messages if 'py.fd' in m])

        gc_expected = [
            'g:py.gc.enabled,pid=7:1',
            'g:py.gc.collections,gen=0,pid=7:10',
            'g:py.gc.collected,gen=0,pid=7:11',
            'g:py.gc.uncollectable,gen=0,pid=7:12',
            'g:py.gc.threshold,gen=0,pid=7:100',
            'g:py.gc.count,gen=0,pid=7:200',
            'g:py.gc.collections,gen=1,pid=7:20',
            'g:py.gc.collected,gen=1,pid=7:21',
            'g:py.gc.uncollectable,gen=1,pid=7:22',
            'g:py.gc.threshold,gen=1,pid=7:101',
            'g:py.gc.count,gen=1,pid=7:201',
            'g:py.gc.collections,gen=2,pid=7:30',
            'g:py.gc.collected,gen=2,pid=7:31',
            'g:py.gc.uncollectable,gen=2,pid=7:32',
            'g:py.gc.threshold,gen=2,pid=7:102',
            'g:py.gc.count,gen=2,pid=7:202',
        ]
        self.assertEqual(gc_expected, [m for m in messages if 'py.gc' in m])

        mp_expected = [
            'g:py.mp.activeChildren,pid=7:0',
            'g:py.os.cpu,pid=7:4',
        ]
        self.assertEqual(mp_expected, [m for m in messages if 'py.mp' in m or 'py.os' in m])

        resource_expected = [
            'g:py.resource.time,mode=user,pid=7:1',
            'g:py.resource.time,mode=system,pid=7:2',
            'g:py.resource.maxResidentSetSize,pid=7:3',
            'g:py.resource.pageFaults,io.required=false,pid=7:4',
            'g:py.resource.pageFaults,io.required=true,pid=7:5',
            'g:py.resource.blockOperations,id=input,pid=7:6',
            'g:py.resource.blockOperations,id=output,pid=7:7',
            'g:py.resource.contextSwitches,id=voluntary,pid=7:8',
            'g:py.resource.contextSwitches,id=involuntary,pid=7:9',
        ]
        self.assertEqual(resource_expected, [m for m in messages if 'py.resource' in m])

        threading_expected = [
            'g:py.threading.active,pid=7:5'
        ]
        self.assertEqual(threading_expected, [m for m in messages if 'py.threading' in m])
