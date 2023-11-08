from datadog import initialize
from datadog.api.metrics import Metric


def send_datadog_metric(options, *args, **kwargs):
    initialize(**options)
    Metric.send(*args, **kwargs)
