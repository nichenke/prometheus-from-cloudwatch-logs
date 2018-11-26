""" Merging Prometheus stats parser.

This is similar to the internals of the pushgateway, but more like the
aggregating one from Weaveworks. The logic was replicated (original in go) to
allow for processing logs and exposing metrics directly without needing an
external pushgateway.

"""

from typing import Any, Iterable, MutableMapping, Sequence, Tuple

# TODO metrics on metric processing
from prometheus_client import CollectorRegistry, Counter, Metric
from prometheus_client.parser import text_string_to_metric_families
from prometheus_client.core import Sample


def sample_id(sample: Sample) -> Tuple[str, Sequence[Any]]:
    """ construct label id from name and labels to allow matching

    Args:
        sample (Sample): sample instance

    Returns:
        tuple: tuple with name and labels as the id
    """
    name = sample.name
    labels = tuple(sample.labels.items()) if sample.labels else ''
    return (name, labels)


def add_counter_samples(old: Sample, new: Sample) -> Sample:
    """ add sample value from new onto old, returning new Sample

    Args:
        old (Sample): original metric sample
        new (Sample): new metric sample

    Returns:
        Sample: new sample instance with combined values

    """
    # Samples are tuples, so need a new one with combined values
    total = old.value + new.value
    combined = Sample(old.name, old.labels, total)
    return combined


def merge_counter(existing: Counter, new: Counter) -> None:
    """ merge two counters by adding values

    Counters have all the same name but potentially different sets of labels.

    Args:
        existing (Counter): counter instance to merge into
        new (Counter): incoming data, merge into existing

    """
    e_samples = {sample_id(s):s for s in existing.samples}
    for sample in new.samples:
        new_id = sample_id(sample)

        if new_id in e_samples:
            old = e_samples[new_id]
            combined = add_counter_samples(old, sample)

            e_samples[new_id] = combined
        else:
            e_samples[new_id] = sample

    existing.samples[:] = e_samples.values()


def merge_samples(existing: Metric, new: Metric) -> None:
    """ merge samples from new into existing

    Args:
        existing (Metric): existing metric instance to merge into
        new (Metric): incoming metric data to consume

    Raises:
        NotImplementedError: issued on metrics not in (Counter, Summary)

    """
    if existing.type == 'counter':
        merge_counter(existing, new)
    elif existing.type == 'summary':
        # The internals of summary are multiple counters, so we can use the existing merging
        # NOTE: Python doesn't support quartiles, so we might have a problem with stats coming in
        # from Java or other locations. Those should blow up on parse...
        merge_counter(existing, new)
    else:
        raise NotImplementedError('only counters for now')


class MergeCollector:
    """ Build up a collection of Metric() instances, combining samples """
    _metrics: MutableMapping = {}


    def add_metrics(self, incoming: Sequence[Metric]) -> None:
        """ for each metric, merge samples to the existing metrics

        Args:
            incoming (Sequence[Metric]): list of metrics to process

        """
        for metric in incoming:
            existing = self._metrics.get(metric.name, None)
            if existing:
                merge_samples(existing, metric)
            else:
                self._metrics[metric.name] = metric


    def collect(self) -> Iterable[Metric]:
        """ yield name sorted metrics for registry API

        Yields:
            Metric: the next metric in our collection
        """
        # pretty sort by name
        names = sorted(self._metrics.keys())

        for name in names:
            metric = self._metrics[name]
            yield metric


# Wire in our collector to a registry and expose it for users. This does not
# add the metrics to the global exported stats, a runtime process needs to do
# that.
MERGER = MergeCollector()
MERGE_REGISTRY = CollectorRegistry()
MERGE_REGISTRY.register(MERGER)

def process_metric_text(text: str) -> None:
    """ process incoming metrics and add to the MergeCollector and
    MERGE_REGISTRY for exposition

    Args:
        text (str): incoming prometheus metrics text to parse
    """
    metrics = text_string_to_metric_families(text)

    # Not interested in the created timestamp for metrics
    metrics = [m for m in metrics if not m.name.endswith('_created')]

    MERGER.add_metrics(metrics)
