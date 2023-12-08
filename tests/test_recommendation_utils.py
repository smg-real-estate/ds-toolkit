import json
from unittest import mock

import numpy as np

from ds_toolkit.recommendations_utils import (
    coalesce,
    convert_to_float,
    convert_to_int,
    deep_get,
    get_category_code,
    get_filter_features,
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


def test_get_filter_features():
    with open("tests/listing.json", "r") as listing_file:
        listing_data = json.loads(listing_file.read())
    filter_data = get_filter_features(listing_data)

    assert filter_data["LISTING_ID"] == "3000209985"
    assert filter_data["COUNTRY"] == "CH"
    assert filter_data["OFFERTYPE"] == "BUY"


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


def test_get_category_code():
    assert get_category_code("HOUSE,SINGLE_HOUSE") == "HOUSE"
    assert (
        get_category_code("UNDERGROUND_SLOT,OVERED_PARKING_PLACE_BIKE")
        == "PARK"
    )


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
    flat_data = get_listing_features(listing_data)

    assert flat_data["LISTING_ID"] == 3000209985
    assert flat_data["PRICE"] == 578000.0
    assert flat_data["SPACE"] == 112.0
    assert flat_data["FLOORSPACE"] is None
    assert flat_data["SINGLEFLOORSPACE"] is None
    assert flat_data["LOTSIZE"] == 800.0
    assert flat_data["NUMBEROFROOMS"] == 6.0
    assert flat_data["FLOOR"] == 3.0
    assert flat_data["NUMBEROFFLOORS"] is None
    assert flat_data["YEARBUILT"] == 1967.0
    assert flat_data["AREPETSALLOWED"] is None
    assert flat_data["HASELEVATOR"] is None
    assert flat_data["HASPARKING"] is None
    assert flat_data["HASGARAGE"] is True
    assert flat_data["HASNICEVIEW"] is True
    assert flat_data["HASSTEAMER"] is None
    assert flat_data["HASWASHINGMACHINE"] is None
    assert flat_data["HASTUMBLEDRYER"] is None
    assert flat_data["HASCABLETV"] is True
    assert flat_data["HASFLATSHARINGCOMMUNITY"] is None
    assert flat_data["ISCHILDFRIENDLY"] is True
    assert flat_data["ISREFURBISHED"] is None
    assert flat_data["YEARLASTRENOVATED"] is None
    assert flat_data["ISWHEELCHAIRACCESSIBLE"] is None
    assert flat_data["ISMINERGIECERTIFIED"] is None
    assert flat_data["ISMINERGIEGENERAL"] is None
    assert flat_data["ISNEWBUILDING"] is None
    assert flat_data["ISOLDBUILDING"] is True
    assert flat_data["ISGROUNDFLOOR"] is None
    assert flat_data["HASATTIC"] is None
    assert flat_data["HASBALCONY"] is True
    assert flat_data["HASGARDENSHED"] is None
    assert flat_data["HASSWIMMINGPOOL"] is None
    assert flat_data["HASFIREPLACE"] is None
    assert flat_data["POSTALCODE"] == 2406
    assert flat_data["CANTON"] == "NE"
    assert flat_data["CATEGORIES"] == "HOUSE,SINGLE_HOUSE"
    assert flat_data["CATEGORY_CODE"] == "HOUSE"
