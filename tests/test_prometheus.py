""" Test the core prometheus metric merging and parsing """

import pytest

from prometheus_client import generate_latest
from prometheus_client.core import (
    CounterMetricFamily, SummaryMetricFamily, Sample
)

from cloudwatch_prom import merger
from cloudwatch_prom.merger import MERGE_REGISTRY, MERGER, process_metric_text

# Ignore common fixture pylint whines
# pylint:disable=redefined-outer-name
# Drop docstring requirements for tests
# pylint:disable=missing-yield-doc,missing-param-doc,missing-return-doc
# pylint:disable=missing-yield-type-doc,missing-type-doc,missing-return-type-doc

SAMPLE_METRICS = """# HELP runtime_seconds Total runtime in seconds
# TYPE runtime_seconds summary
runtime_seconds_count 1.0
runtime_seconds_sum 0.272285345
# TYPE runtime_seconds_created gauge
runtime_seconds_created 1543016308.196686
# HELP message_types_total Message counts by time
# TYPE message_types_total counter
message_types_total{format="text"} 1.0
message_types_total{format="json"} 1.0
# TYPE message_types_created gauge
message_types_created{format="text"} 1543016308.468988
message_types_created{format="json"} 1543016308.469216
"""


@pytest.fixture(autouse=True)
def test_collector(mocker):
    """ Use a clean collector for each test """
    mocker.patch.object(MERGER, '_metrics', new_callable=dict)
    yield MERGE_REGISTRY


def test_sample_id():
    """ construct sample_id and validate it is correct """
    sample = Sample('sample_name', {}, 22)
    sid = merger.sample_id(sample)

    assert sid == ('sample_name', '')


def test_sample_id_labels():
    """ construct sample_id and validate it is correct """
    sample = Sample('sample_name', {'foo': 1234, 'bar': 'yes'}, 22)
    sid = merger.sample_id(sample)

    assert sid == ('sample_name', (('foo', 1234), ('bar', 'yes')))


def test_add_counters():
    """ add two counter samples """
    sample1 = Sample('first', {}, 22)
    sample2 = Sample('second', {}, 44.1)

    total = merger.add_counter_samples(sample1, sample2)
    assert total.name == 'first'
    assert not total.labels
    assert total.value == 66.1


def test_merge_counter():
    """ test normal adding of two counter metrics """
    count = CounterMetricFamily('message_types', 'Message counts by time', labels=['format'])
    count.add_metric(['text'], 1.0)
    count.add_metric(['json'], 1.0)

    wanted = CounterMetricFamily('message_types', 'Message counts by time', labels=['format'])
    wanted.add_metric(['text'], 2.0)
    wanted.add_metric(['json'], 2.0)

    merger.merge_counter(count, count)

    assert count == wanted


def test_merge_counter_labels():
    """ test blending of two metrics with different labels """
    count1 = CounterMetricFamily('message_types', 'Message counts by time', labels=['format'])
    count1.add_metric(['text'], 1.0)

    count2 = CounterMetricFamily('message_types', 'Message counts by time', labels=['format'])
    count2.add_metric(['json'], 1.0)

    wanted = CounterMetricFamily('message_types', 'Message counts by time', labels=['format'])
    wanted.add_metric(['text'], 1.0)
    wanted.add_metric(['json'], 1.0)

    merger.merge_counter(count1, count2)

    assert count1 == wanted


def test_basic_parse(test_collector):
    """ parse metrics and validate we get metrics created correctly """
    process_metric_text(SAMPLE_METRICS)

    # for posterity and debugging
    output = generate_latest(registry=test_collector).decode()
    print(output)

    # ref: https://github.com/prometheus/client_python/blob/master/tests/test_parser.py
    metrics = list(test_collector.collect())

    counts = CounterMetricFamily('message_types', 'Message counts by time', labels=['format'])
    counts.add_metric(['text'], 1.0)
    counts.add_metric(['json'], 1.0)

    runtime = SummaryMetricFamily('runtime_seconds', 'Total runtime in seconds',
                                  count_value=1, sum_value=0.272285345)
    wanted = [counts, runtime]

    assert wanted == metrics


def test_basic_merge(test_collector):
    """ test adding the same metrics to itself and validating the counts """
    # Same, but twice
    process_metric_text(SAMPLE_METRICS)
    process_metric_text(SAMPLE_METRICS)

    metrics = list(test_collector.collect())

    counts = CounterMetricFamily('message_types', 'Message counts by time', labels=['format'])
    counts.add_metric(['text'], 2.0)
    counts.add_metric(['json'], 2.0)

    runtime = SummaryMetricFamily('runtime_seconds', 'Total runtime in seconds',
                                  count_value=2, sum_value=0.272285345*2)
    wanted = [counts, runtime]

    assert wanted == metrics
