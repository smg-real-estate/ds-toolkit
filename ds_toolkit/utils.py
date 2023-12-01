import pickle
from io import BytesIO
from typing import Any

from botocore.client import BaseClient
from datadog import initialize
from datadog.api.metrics import Metric


def send_datadog_metric(options, *args, **kwargs):
    initialize(**options)
    Metric.send(*args, **kwargs)


def dump_object_to_s3(client: BaseClient, obj: Any, bucket: str, key: str):
    """
    Dump an object to S3

    :param client: S3 client
    :param obj: Object to dump
    :param bucket: S3 bucket
    :param key: S3 key
    :return: None
    """
    buff = BytesIO()
    buff.write(pickle.dumps(obj))
    buff.seek(0)

    client.put_object(
        Body=buff.read(),
        Bucket=bucket,
        Key=key,
    )


def load_object_from_s3(client: BaseClient, bucket: str, key: str) -> Any:
    """
    Load an object from S3

    :param client: S3 client
    :param bucket: S3 bucket
    :param key: S3 key
    :return: Loaded object
    """
    buff = client.get_object(
        Bucket=bucket,
        Key=key,
    )["Body"].read()
    return pickle.loads(buff)
