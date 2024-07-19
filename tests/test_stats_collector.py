import unittest.mock

from spectator.config import Config
from spectator.registry import Registry

from runmetrics.stats_collector import StatsCollector


class MockStatsCollector(StatsCollector):
    def _collect_fd_stats(self):
        self._fd_max.set(100)

    def _collect_gc_stats(self):
        self._gc_enabled.set(200)

        for i in range(0, 3):
            self._gc_gen[i]["collections"].set(201)
            self._gc_gen[i]["collected"].set(202)
            self._gc_gen[i]["uncollectable"].set(203)
            self._gc_gen[i]["threshold"].set(204)
            self._gc_gen[i]["count"].set(205)

    def _collect_mp_stats(self):
        self._mp_active_children.set(300)
        self._mp_cpu.set(301)

    def _collect_resource_stats(self):
        self._ru_utime.set(400)
        self._ru_stime.set(401)
        self._ru_maxrss.set(402)
        self._ru_minflt.set(403)
        self._ru_majflt.set(404)
        self._ru_inblock.set(405)
        self._ru_oublock.set(406)
        self._ru_nvcsw.set(407)
        self._ru_nivcsw.set(408)

    def _collect_threading_stats(self):
        self._threading_active.set(500)


@unittest.mock.patch("os.getpid", return_value=1)
class StatsCollectorTest(unittest.TestCase):
    def test_collect_stats(self, mock_getpid):
        r = Registry(Config("memory"))
        MockStatsCollector(r).collect_stats()
        self.assertEqual(29, len(r.writer().get()))

        expected = [
            'g:py.fd,id=max:100',
            'g:py.gc.enabled:200',
            'g:py.gc.collections,gen=0:201',
            'g:py.gc.collected,gen=0:202',
            'g:py.gc.uncollectable,gen=0:203',
            'g:py.gc.threshold,gen=0:204',
            'g:py.gc.count,gen=0:205',
            'g:py.gc.collections,gen=1:201',
            'g:py.gc.collected,gen=1:202',
            'g:py.gc.uncollectable,gen=1:203',
            'g:py.gc.threshold,gen=1:204',
            'g:py.gc.count,gen=1:205',
            'g:py.gc.collections,gen=2:201',
            'g:py.gc.collected,gen=2:202',
            'g:py.gc.uncollectable,gen=2:203',
            'g:py.gc.threshold,gen=2:204',
            'g:py.gc.count,gen=2:205',
            'g:py.mp.activeChildren:300',
            'g:py.mp.cpu:301',
            'g:py.resource.time,mode=user:400',
            'g:py.resource.time,mode=system:401',
            'g:py.resource.maxResidentSetSize:402',
            'g:py.resource.pageFaults,io.required=false:403',
            'g:py.resource.pageFaults,io.required=true:404',
            'g:py.resource.blockOperations,id=input:405',
            'g:py.resource.blockOperations,id=output:406',
            'g:py.resource.contextSwitches,id=voluntary:407',
            'g:py.resource.contextSwitches,id=involuntary:408',
            'g:py.threading.active,pid=1:500'
        ]
        self.assertEqual(expected, r.writer().get())
