import json
from unittest import mock

import numpy as np

from ds_toolkit.recommendations_utils import (
    coalesce,
    convert_to_float,
    convert_to_int,
    deep_get,
    get_listing_features,
    get_recommendations_ordered_by_distance,
    is_acceptable_recommendation,
    isnull,
    normalise_price,
)


@mock.patch("ds_toolkit.recommendations_utils.distance")
def test_is_acceptable_recommendation(mock_distance):
    mock_distance.return_value = lambda: None
    mock_distance.return_value.km = 5.0

    source_listing = {
        "LISTING_ID": 1,
        "LATITUDE": 47.3769,
        "LONGITUDE": 8.5417,
        "CATEGORIES": "HOUSE,SINGLE_HOUSE",
        "IS_ACTIVE": True,
    }

    target_listing = {
        "LISTING_ID": 2,
        "LATITUDE": 43.3769,
        "LONGITUDE": 8.5417,
        "CATEGORIES": "HOUSE",
        "IS_ACTIVE": True,
    }

    assert (
        is_acceptable_recommendation(source_listing, 10.0, target_listing)
        is True
    )
    assert (
        is_acceptable_recommendation(
            source_listing, 10.0, {**target_listing, "IS_ACTIVE": False}
        )
        is False
    )
    assert (
        is_acceptable_recommendation(
            source_listing, 10.0, {**target_listing, "CATEGORIES": "GARAGE"}
        )
        is False
    )
    assert (
        is_acceptable_recommendation(source_listing, 3.0, target_listing)
        is False
    )


def test_get_recommendations_ordered_by_distance():
    recommended_listing_ids_map = {
        1: [(20, 0.1), (30, 0.3)],
        2: [(20, 0.3), (50, 0.05)],
        3: [(60, 0.2)],
    }
    assert get_recommendations_ordered_by_distance(
        recommended_listing_ids_map, [1]
    ) == [20, 30]
    assert get_recommendations_ordered_by_distance(
        recommended_listing_ids_map, [2]
    ) == [50, 20]
    assert get_recommendations_ordered_by_distance(
        recommended_listing_ids_map, [1, 2, 3]
    ) == [50, 20, 60, 30]


def test_deep_get():
    assert deep_get({"a": {"b": 10}}, "a.b") == 10
    assert deep_get({"a": {"b": 10}}, "c.b") is None
    assert deep_get({"a": {"b": 10}}, "a.c") is None
    assert deep_get({"a": {"b": 10}}, "c") is None
    assert deep_get({"a": {"b": 10}}, "c", "D") == "D"


def test_isnull():
    assert isnull(None)
    assert isnull(np.nan)
    assert isnull([])
    assert not isnull("abc")
    assert not isnull("")
    assert not isnull(0)
    assert not isnull(5)
    assert not isnull(5.0)
    assert not isnull(np.float64(5.1))
    assert not isnull(float(5.1))


def test_convert_to_int():
    assert convert_to_int("3000209985") == 3000209985
    assert convert_to_int(np.nan) is None
    assert convert_to_int(None) is None


def test_convert_to_float():
    assert convert_to_float(3) == 3.0
    assert convert_to_float(np.nan) is None
    assert convert_to_float(None) is None


def test_coalesce():
    assert coalesce(3, 4) == 3
    assert coalesce(None, 4) == 4
    assert coalesce(None, None) is None
    assert coalesce(None, None, 5) == 5


def test_normalise_price():
    with open("tests/rent_m2_y.json", "r") as listing_file:
        listing_data = json.loads(listing_file.read())
    assert normalise_price(listing_data) == 8887.5

    with open("tests/rent_all_w.json", "r") as listing_file:
        listing_data = json.loads(listing_file.read())
    assert normalise_price(listing_data) == 3033.33


def test_get_listing_features():
    with open("tests/listing.json", "r") as listing_file:
        listing_data = json.loads(listing_file.read())
    listing_features = get_listing_features(listing_data)

    assert listing_features["LISTING_ID"] == 3000209985
    assert listing_features["COUNTRY"] == "CH"
    assert listing_features["OFFERTYPE"] == "BUY"
    assert listing_features["PRICE"] == 578000.0
    assert listing_features["LATITUDE"] == 46.9821324
    assert listing_features["LONGITUDE"] == 6.607183900000001
    assert listing_features["SPACE"] == 112.0
    assert listing_features["FLOORSPACE"] is None
    assert listing_features["SINGLEFLOORSPACE"] is None
    assert listing_features["LOTSIZE"] == 800.0
    assert listing_features["NUMBEROFROOMS"] == 6.0
    assert listing_features["FLOOR"] == 3.0
    assert listing_features["NUMBEROFFLOORS"] is None
    assert listing_features["YEARBUILT"] == 1967.0
    assert listing_features["AREPETSALLOWED"] is None
    assert listing_features["HASELEVATOR"] is None
    assert listing_features["HASPARKING"] is None
    assert listing_features["HASGARAGE"] is True
    assert listing_features["HASNICEVIEW"] is True
    assert listing_features["HASSTEAMER"] is None
    assert listing_features["HASWASHINGMACHINE"] is None
    assert listing_features["HASTUMBLEDRYER"] is None
    assert listing_features["HASCABLETV"] is True
    assert listing_features["HASFLATSHARINGCOMMUNITY"] is None
    assert listing_features["ISCHILDFRIENDLY"] is True
    assert listing_features["ISREFURBISHED"] is None
    assert listing_features["YEARLASTRENOVATED"] is None
    assert listing_features["ISWHEELCHAIRACCESSIBLE"] is None
    assert listing_features["ISMINERGIECERTIFIED"] is None
    assert listing_features["ISMINERGIEGENERAL"] is None
    assert listing_features["ISNEWBUILDING"] is None
    assert listing_features["ISOLDBUILDING"] is True
    assert listing_features["ISGROUNDFLOOR"] is None
    assert listing_features["HASATTIC"] is None
    assert listing_features["HASBALCONY"] is True
    assert listing_features["HASGARDENSHED"] is None
    assert listing_features["HASSWIMMINGPOOL"] is None
    assert listing_features["HASFIREPLACE"] is None
    assert listing_features["POSTALCODE"] == 2406
    assert listing_features["CANTON"] == "NE"
    assert listing_features["CATEGORIES"] == "HOUSE,SINGLE_HOUSE"
    assert listing_features["CATEGORY_CODE"] == "HOUSE"
