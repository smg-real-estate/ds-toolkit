from datadog import api, initialize


def send_datadog_metric(options, *args, **kwargs):
    initialize(**options)
    api.Metric.send(*args, **kwargs)
