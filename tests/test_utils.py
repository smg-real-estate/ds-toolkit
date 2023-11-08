from unittest import mock

from ds_toolkit.utils import send_datadog_metric


@mock.patch("ds_toolkit.utils.initialize")
@mock.patch("ds_toolkit.utils.Metric.send")
def test_send_datadog_metric(mock_send, mock_initialize):
    datadog_options = {
        "api_key": "datadog_api_key",
        "app_key": "datadog_app_key",
        "api_host": "datadog_api_host",
    }
    send_datadog_metric(
        datadog_options,
        tags=["test:1"],
        metric="test.metric",
        points=[(1, 1)],
    )
    mock_send.assert_called_once_with(
        tags=["test:1"], metric="test.metric", points=[(1, 1)]
    )
    mock_initialize.assert_called_once_with(**datadog_options)
