import json
import pickle
from enum import Enum
from io import BytesIO, StringIO
from typing import Any

from botocore.client import BaseClient
from datadog import initialize
from datadog.api.metrics import Metric


def send_datadog_metric(options, *args, **kwargs):
    initialize(**options)
    Metric.send(*args, **kwargs)


class ObjectFormat(Enum):
    """
    Enum to define the format of the object
    """

    PICKLE = "pickle"
    JSON = "json"


def dump_object_to_s3(
    client: BaseClient,
    obj: Any,
    bucket: str,
    key: str,
    format: ObjectFormat = ObjectFormat.PICKLE,
):
    """
    Dump an object to S3

    :param client: S3 client
    :param obj: Object to dump
    :param bucket: S3 bucket
    :param key: S3 key
    :param format: Format of the object, can be pickle or json
    :return: None
    """
    if format == ObjectFormat.PICKLE:
        buff = BytesIO()
        buff.write(pickle.dumps(obj))
    elif format == ObjectFormat.JSON:
        buff = StringIO()
        json.dump(obj, buff)
    buff.seek(0)

    client.put_object(
        Body=buff.read(),
        Bucket=bucket,
        Key=key,
    )


def load_object_from_s3(
    client: BaseClient,
    bucket: str,
    key: str,
    format: ObjectFormat = ObjectFormat.PICKLE,
) -> Any:
    """
    Load an object from S3

    :param client: S3 client
    :param bucket: S3 bucket
    :param key: S3 key
    :param format: Format of the object, can be pickle or json
    :return: Loaded object
    """
    buff = client.get_object(
        Bucket=bucket,
        Key=key,
    )["Body"].read()
    if format == ObjectFormat.PICKLE:
        return pickle.loads(buff)
    elif format == ObjectFormat.JSON:
        return json.loads(buff)
