from unittest import mock

from ds_toolkit.utils import (
    dump_object_to_s3,
    load_object_from_s3,
    send_datadog_metric,
)


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


@mock.patch("ds_toolkit.utils.pickle.dumps")
@mock.patch("ds_toolkit.utils.BytesIO")
def test_dump_object_to_s3(mock_bytesio, mock_dumps):
    mock_client = mock.MagicMock()
    mock_obj = mock.MagicMock()
    mock_bucket = mock.MagicMock()
    mock_key = mock.MagicMock()
    mock_buff = mock.MagicMock()
    mock_bytesio.return_value = mock_buff
    mock_dumps.return_value = "pickled_obj"
    mock_buff.read.return_value = "pickled_obj"

    dump_object_to_s3(mock_client, mock_obj, mock_bucket, mock_key)
    mock_bytesio.assert_called_once_with()
    mock_dumps.assert_called_once_with(mock_obj)
    mock_buff.write.assert_called_once_with("pickled_obj")
    mock_buff.seek.assert_called_once_with(0)
    mock_client.put_object.assert_called_once_with(
        Body="pickled_obj", Bucket=mock_bucket, Key=mock_key
    )


@mock.patch("ds_toolkit.utils.pickle.loads")
def test_load_object_from_s3(mock_loads):
    mock_client = mock.MagicMock()
    mock_bucket = mock.MagicMock()
    mock_key = mock.MagicMock()
    mock_obj = mock.MagicMock()
    mock_client.get_object.return_value = {"Body": mock_obj}
    mock_obj.read.return_value = "pickled_obj"
    mock_loads.return_value = "unpickled_obj"

    assert (
        load_object_from_s3(mock_client, mock_bucket, mock_key)
        == "unpickled_obj"
    )
    mock_client.get_object.assert_called_once_with(
        Bucket=mock_bucket, Key=mock_key
    )
    mock_obj.read.assert_called_once_with()
    mock_loads.assert_called_once_with("pickled_obj")
