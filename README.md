[![Snapshot](https://github.com/Netflix/spectator-py-runtime-metrics/actions/workflows/snapshot.yml/badge.svg)](https://github.com/Netflix/spectator-py-runtime-metrics/actions/workflows/snapshot.yml) [![PyPI version](https://badge.fury.io/py/netflix-spectator-py-runtime-metrics.svg)](https://badge.fury.io/py/netflix-spectator-py-runtime-metrics)

## spectator-py-runtime-metrics

Library to collect runtime metrics for Python applications using [spectator-py](https://github.com/Netflix/spectator-py).

See the [Atlas Documentation] site for more details on `spectator-py`.

[Atlas Documentation]: https://netflix.github.io/atlas-docs/spectator/lang/py/usage/

## Instrumenting Code

```python
from spectator.registry import Registry
from runmetrics.stats_collector import StatsCollector

if __name__ == "__main__":
    registry = Registry()
    # optionally add a stable worker id tag to runtime metrics, for forked processes
    StatsCollector(registry, worker_id=None).start()
```

## Worker IDs

For long-running Python applications, it is common to use a forking process model to increase the
ability to handle load. Usually, these rely upon the `pid` to uniquely identify the workers, but
some of these frameworks offer either a stable worker id or the ability to create stable worker id
values through the addition of callbacks.

Ideally, the worker id is a string in the range `0..N`, with `N<16` in most cases. Most process
forking frameworks have a configuration setting for the maximum number of workers, which helps to
keep these values constrained.

Using raw `str(os.getpid())` values as the worker id is not recommended, because it can lead to large
increases in metrics volume in the Atlas backend, if processes restart regularly over the lifetime of
an instance.

## References

* Python
    * [gc — Garbage Collector interface](https://docs.python.org/3/library/gc.html)
    * [multiprocessing — Process-based parallelism](https://docs.python.org/3/library/multiprocessing.html)
    * [os — Miscellaneous operating system interfaces](https://docs.python.org/3/library/os.html)
    * [resource — Resource usage information](https://docs.python.org/3/library/resource.html)
    * [threading — Thread-based parallelism](https://docs.python.org/3/library/threading.html)
* Linux
    * [getrusage(2) — Linux manual page](https://man7.org/linux/man-pages/man2/getrusage.2.html)

## Local Development

Install [pyenv](https://github.com/pyenv/pyenv), possibly with [Homebrew](https://brew.sh/), and
install a recent Python version.

```shell
make setup-venv
make test
make coverage
```
