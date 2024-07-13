from spectator.registry import Registry


def collect_runtime_metrics(registry: Registry):
    """Start the collection of memory and file handle metrics."""
    collect_mem_stats()
    collect_sys_stats()
