import pickle
from typing import Any, Optional

import numpy as np


def get_cosine_similarity(source_vector, item_representations):
    """
    Function calculates cosine similarity between a source vector
    and a matrix aka item representations.
    Returns a vector of similarity scores with all items in the matrix.
    """
    sim = item_representations.dot(source_vector)
    item_norms = np.linalg.norm(item_representations, axis=1)
    item_vec_norm = np.linalg.norm(source_vector)
    scores = np.squeeze(sim / item_norms / item_vec_norm)
    return scores


def filter_scores_below_treshold(scores, threshold=0.8):
    """
    Function filters out similarity scores below the treshold.
    Default threshold is 0.8.

    Returns a list of indices of the most similar items in
    descending order without the first item (the item itself).
    """
    (idx,) = np.where(scores > threshold)
    return idx[np.argsort(-scores[idx])][1:]


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    Code stolen from: https://stackoverflow.com/a/26853961
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def get_recommendations_ordered_by_distance(
    model_id_to_ids, listing_ids, reverse=False
):
    """
    merge recommendations for each listing
    ordering is done using distance to corresponding listing
    the final list is deduplicated
    return list of ids
    """
    recommended_listing = []
    for listing_id in listing_ids:
        recommended_listing.extend(model_id_to_ids.get(listing_id, []))
    recommended_listing.sort(key=lambda id_dist: id_dist[1], reverse=reverse)
    seen = set()
    recommended_listing_ids = []
    for listing_id in [listing_id for (listing_id, _) in recommended_listing]:
        if listing_id not in seen:
            recommended_listing_ids.append(listing_id)
            seen.add(listing_id)
    return recommended_listing_ids


def deep_get(input_dict, object_path, default_value=None, separator="."):
    """
    Performs a deep get on a dictionary, returning the value at the specified
    path. If the path does not exist, the default value is returned.
    By default, the path components are separated by a dot, but this can be
    changed by specifying the separator parameter.
    """

    def _deep_get(d, path_components):
        if len(path_components) == 1:
            return d.get(path_components[0], default_value)
        else:
            if path_components[0] in d:
                return _deep_get(d[path_components[0]], path_components[1:])
            else:
                return default_value

    return _deep_get(input_dict, object_path.split(separator))


def filter_hgrets(listing_info):
    """
    Returns a smaller subset of the listing info, containing only the fields:
    - id as listing_id
    - address.country as listing_address_country
    - offerType as listing_offertype
    """
    return {
        "listing_id": deep_get(listing_info, "listing.id"),
        "listing_address_country": deep_get(
            listing_info, "listing.address.country"
        ),
        "listing_offertype": deep_get(listing_info, "listing.offerType"),
    }


def isnull(value: Any) -> bool:
    """
    Function to check if a value is null or not.
    Returns True if the value is null, False otherwise.
    """
    if isinstance(value, str):
        return False
    elif isinstance(value, list):
        return len(value) == 0
    elif isinstance(value, np.float64):
        return np.isnan(value)
    elif isinstance(value, float):
        return np.isnan(value)
    else:
        return value is None


def convert_to_int(value: Any) -> Optional[int]:
    """
    Safely converts a value to an integer.
    """
    if isnull(value):
        return None
    return int(value)


def convert_to_float(value: Any) -> Optional[float]:
    """
    Safely converts a value to a float.
    """
    if isnull(value):
        return None
    return float(value)


def coalesce(first_val, second_val, third_val=None):
    """
    Returns the first non-null value from the provided values.
    """
    if not isnull(first_val):
        return first_val
    elif not isnull(second_val):
        return second_val
    elif not isnull(third_val):
        return third_val
    else:
        return None


def normalise_price(listing_info):
    """
    Normalises the price of a listing to a monthly price.
    """
    offer_type = deep_get(listing_info, "listing.offerType")
    living_space = deep_get(
        listing_info, "listing.characteristics.livingSpace"
    )
    total_floor_space = deep_get(
        listing_info, "listing.characteristics.totalFloorSpace"
    )
    lotsize = deep_get(listing_info, "listing.characteristics.lotSize")
    space = coalesce(living_space, total_floor_space, lotsize)
    price_rent_area = deep_get(listing_info, "listing.prices.rent.area")
    price_rent_gross = deep_get(listing_info, "listing.prices.rent.gross")
    price_buy_price = deep_get(listing_info, "listing.prices.buy.price")

    if (
        offer_type == "RENT"
        and price_rent_area != "KM2"
        and price_rent_gross is not None
        and not isnull(price_rent_gross)
        and price_rent_gross > 0
    ):
        price_rent_interval = deep_get(
            listing_info, "listing.prices.rent.interval"
        )

        if price_rent_interval == "DAY" and space is None:
            price = price_rent_gross * 365 / 12
        elif price_rent_interval == "YEAR" and price_rent_area != "M2":
            price = price_rent_gross / 12
        elif (
            price_rent_interval == "MONTH" or price_rent_interval == "ONETIME"
        ):
            price = price_rent_gross
        elif price_rent_interval == "WEEK":
            price = price_rent_gross * 52 / 12
        elif space is None:
            raise ValueError(
                f"Space is undefined for listing {listing_info['id']}"
            )
        elif (
            price_rent_interval == "YEAR"
            and price_rent_area == "M2"
            and space > 0
        ):
            price = price_rent_gross * space / 12
        elif (
            (
                price_rent_interval == "MONTH"
                or price_rent_interval == "ONETIME"
            )
            and price_rent_area == "M2"
            and space > 0
        ):
            price = price_rent_gross * space
        elif (
            price_rent_interval == "WEEK"
            and price_rent_area == "M2"
            and space > 0
        ):
            price = price_rent_gross * space * 52 / 12
        elif (
            price_rent_interval == "DAY"
            and price_rent_area == "M2"
            and space > 0
        ):
            price = price_rent_gross * space * 365 / 12
        else:
            price = None

    elif (
        offer_type == "BUY"
        and price_buy_price is not None
        and not isnull(price_buy_price)
        and price_buy_price > 0
    ):
        price_buy_area = deep_get(listing_info, "listing.prices.buy.area")
        if price_buy_area == "M2" and space is not None and space > 0:
            price = price_buy_price * space
        elif price_buy_area == "ALL" or isnull(price_buy_area):
            price = price_buy_price
        else:
            price = None
    else:
        price = None

    if price is not None:
        return float("{:.2f}".format(price))
    else:
        return None


def flatten_hgrets(listing_info):
    """
    Returns a smaller subset of the listing info, containing only the fields:
    - id as LISTING_ID
    - prices.rent.gross as PRICE
    - characteristics.livingSpace as SPACE
    - characteristics.totalFloorSpace as FLOORSPACE
    - characteristics.singleFloorSpace as SINGLEFLOORSPACE
    - characteristics.lotSize as LOTSIZE
    - characteristics.numberOfRooms as NUMBEROFROOMS
    - characteristics.floor as FLOOR
    - characteristics.numberOfFloors as NUMBEROFFLOORS
    - characteristics.yearBuilt as YEARBUILT
    - characteristics.arePetsAllowed as AREPETSALLOWED
    - characteristics.hasElevator as HASELEVATOR
    - characteristics.hasParking as HASPARKING
    - characteristics.hasGarage as HASGARAGE
    - characteristics.hasNiceView as HASNICEVIEW
    - characteristics.hasSteamer as HASSTEAMER
    - characteristics.hasWashingMachine as HASWASHINGMACHINE
    - characteristics.hasTumbleDryer as HASTUMBLEDRYER
    - characteristics.hasCableTv as HASCABLETV
    - characteristics.hasFlatSharingCommunity as HASFLATSHARINGCOMMUNITY
    - characteristics.isChildFriendly as ISCHILDFRIENDLY
    - characteristics.isRefurbished as ISREFURBISHED
    - characteristics.yearLastRenovated as YEARLASTRENOVATED
    - characteristics.isWheelchairAccessible as ISWHEELCHAIRACCESSIBLE
    - characteristics.isMinergieCertified as ISMINERGIECERTIFIED
    - characteristics.isMinergieGeneral as ISMINERGIEGENERAL
    - characteristics.isNewBuilding as ISNEWBUILDING
    - characteristics.isOldBuilding as ISOLDBUILDING
    - characteristics.isGroundFloor as ISGROUNDFLOOR
    - characteristics.hasAttic as HASATTIC
    - characteristics.hasBalcony as HASBALCONY
    - characteristics.hasGardenShed as HASGARDENSHED
    - characteristics.hasSwimmingPool as HASSWIMMINGPOOL
    - characteristics.hasFireplace as HASFIREPLACE
    - address.postalCode as POSTALCODE
    - address.region as CANTON
    - categories as CATEGORIES
    - categories[0] as CATEGORY_CODE
    """
    return {
        "LISTING_ID": convert_to_int(deep_get(listing_info, "listing.id")),
        "PRICE": normalise_price(listing_info),
        "SPACE": convert_to_float(
            deep_get(listing_info, "listing.characteristics.livingSpace")
        ),
        "FLOORSPACE": convert_to_float(
            deep_get(listing_info, "listing.characteristics.totalFloorSpace")
        ),
        "SINGLEFLOORSPACE": convert_to_float(
            deep_get(listing_info, "listing.characteristics.singleFloorSpace")
        ),
        "LOTSIZE": convert_to_float(
            deep_get(listing_info, "listing.characteristics.lotSize")
        ),
        "NUMBEROFROOMS": convert_to_float(
            deep_get(listing_info, "listing.characteristics.numberOfRooms")
        ),
        "FLOOR": convert_to_float(
            deep_get(listing_info, "listing.characteristics.floor")
        ),
        "NUMBEROFFLOORS": convert_to_float(
            deep_get(listing_info, "listing.characteristics.numberOfFloors")
        ),
        "YEARBUILT": convert_to_float(
            deep_get(listing_info, "listing.characteristics.yearBuilt")
        ),
        "AREPETSALLOWED": deep_get(
            listing_info, "listing.characteristics.arePetsAllowed"
        ),
        "HASELEVATOR": deep_get(
            listing_info, "listing.characteristics.hasElevator"
        ),
        "HASPARKING": deep_get(
            listing_info, "listing.characteristics.hasParking"
        ),
        "HASGARAGE": deep_get(
            listing_info, "listing.characteristics.hasGarage"
        ),
        "HASNICEVIEW": deep_get(
            listing_info, "listing.characteristics.hasNiceView"
        ),
        "HASSTEAMER": deep_get(
            listing_info, "listing.characteristics.hasSteamer"
        ),
        "HASWASHINGMACHINE": deep_get(
            listing_info, "listing.characteristics.hasWashingMachine"
        ),
        "HASTUMBLEDRYER": deep_get(
            listing_info, "listing.characteristics.hasTumbleDryer"
        ),
        "HASCABLETV": deep_get(
            listing_info, "listing.characteristics.hasCableTv"
        ),
        "HASFLATSHARINGCOMMUNITY": deep_get(
            listing_info, "listing.characteristics.hasFlatSharingCommunity"
        ),
        "ISCHILDFRIENDLY": deep_get(
            listing_info, "listing.characteristics.isChildFriendly"
        ),
        "ISREFURBISHED": deep_get(
            listing_info, "listing.characteristics.isRefurbished"
        ),
        "YEARLASTRENOVATED": convert_to_float(
            deep_get(listing_info, "listing.characteristics.yearLastRenovated")
        ),
        "ISWHEELCHAIRACCESSIBLE": deep_get(
            listing_info, "listing.characteristics.isWheelchairAccessible"
        ),
        "ISMINERGIECERTIFIED": deep_get(
            listing_info, "listing.characteristics.isMinergieCertified"
        ),
        "ISMINERGIEGENERAL": deep_get(
            listing_info, "listing.characteristics.isMinergieGeneral"
        ),
        "ISNEWBUILDING": deep_get(
            listing_info, "listing.characteristics.isNewBuilding"
        ),
        "ISOLDBUILDING": deep_get(
            listing_info, "listing.characteristics.isOldBuilding"
        ),
        "ISGROUNDFLOOR": deep_get(
            listing_info, "listing.characteristics.isGroundFloor"
        ),
        "HASATTIC": deep_get(listing_info, "listing.characteristics.hasAttic"),
        "HASBALCONY": deep_get(
            listing_info, "listing.characteristics.hasBalcony"
        ),
        "HASGARDENSHED": deep_get(
            listing_info, "listing.characteristics.hasGardenShed"
        ),
        "HASSWIMMINGPOOL": deep_get(
            listing_info, "listing.characteristics.hasSwimmingPool"
        ),
        "HASFIREPLACE": deep_get(
            listing_info, "listing.characteristics.hasFireplace"
        ),
        "POSTALCODE": convert_to_int(
            deep_get(listing_info, "listing.address.postalCode")
        ),
        "CANTON": deep_get(listing_info, "listing.address.region"),
        "CATEGORIES": ",".join(
            deep_get(listing_info, "listing.categories", [])
        ),
        "CATEGORY_CODE": get_category_code(
            deep_get(listing_info, "listing.categories", [])[0]
        ),
    }


category_to_code = {
    "FARM": "AGRI",
    "AGRICULTURAL_INSTALLATION": "AGRI",
    "MOUNTAIN_FARM": "AGRI",
    "TERRACE_FLAT": "APPT",
    "ATTIC": "APPT",
    "ATTIC_FLAT": "APPT",
    "ROOF_FLAT": "APPT",
    "SINGLE_ROOM": "APPT",
    "DUPLEX": "APPT",
    "FURNISHED_FLAT": "APPT",
    "STUDIO": "APPT",
    "APARTMENT": "APPT",
    "LOFT": "APPT",
    "SHARED_APARTMENT": "APPT",
    "BACHELOR_FLAT": "APPT",
    "ALOTTMENT_GARDEN": "GARDEN",
    "MOVIE_THEATER": "GASTRO",
    "CLUB_DISCO": "GASTRO",
    "CASINO": "GASTRO",
    "RESTAURANT": "GASTRO",
    "TENNIS_COURT": "GASTRO",
    "HOTEL": "GASTRO",
    "CAMPGROUND": "GASTRO",
    "SQUASH_BADMINTON": "GASTRO",
    "INDOOR_TENNIS_COURT": "GASTRO",
    "OUTDOOR_SWIMMING_POOL": "GASTRO",
    "COFFEEHOUSE": "GASTRO",
    "BAR": "GASTRO",
    "INDOOR_SWIMMING_POOL": "GASTRO",
    "GOLF_COURSE": "GASTRO",
    "PUB": "GASTRO",
    "SPORTS_HALL": "GASTRO",
    "MOTEL": "GASTRO",
    "NA_HOLI_0": "HOLI",
    "NA_HOLI_1": "HOLI",
    "NA_HOLI_4": "HOLI",
    "NA_HOLI_2": "HOLI",
    "NA_HOLI_3": "HOLI",
    "CASTLE": "HOUSE",
    "SINGLE_HOUSE": "HOUSE",
    "CHALET": "HOUSE",
    "CAVE_HOUSE": "HOUSE",
    "RUSTICO": "HOUSE",
    "MULTIPLE_DWELLING": "HOUSE",
    "NA_HOUSE_8": "HOUSE",
    "VILLA": "HOUSE",
    "FARM_HOUSE": "HOUSE",
    "ROW_HOUSE": "HOUSE",
    "GRANNY_FLAT": "HOUSE",
    "BIFAMILIAR_HOUSE": "HOUSE",
    "TERRACE_HOUSE": "HOUSE",
    "CHEESE_FACTORY": "INDUS",
    "FACTORY": "INDUS",
    "GARDENING": "INDUS",
    "ADVERTISING_AREA": "INDUS",
    "COMMERCIAL": "INDUS",
    "SAUNA": "INDUS",
    "OLD_AGE_HOME": "INDUS",
    "HAIRDRESSER": "INDUS",
    "SANATORIUM": "INDUS",
    "DISPLAY_WINDOW": "INDUS",
    "INDUSTRIAL_OBJECT": "INDUS",
    "WORKSHOP": "INDUS",
    "SHOPPING_CENTRE": "INDUS",
    "SOLARIUM": "INDUS",
    "INSTITUTION": "INDUS",
    "LABORATORY": "INDUS",
    "RESIDENTIAL_COMMERCIAL_BUILDING": "INDUS",
    "STORAGE_ROOM": "INDUS",
    "KIOSK": "INDUS",
    "PARKING_SPACE": "INDUS",
    "PRACTICE": "INDUS",
    "PARTY_ROOM": "INDUS",
    "ATELIER": "INDUS",
    "SHOP": "INDUS",
    "LIBRARY": "INDUS",
    "RIDING_HALL": "INDUS",
    "ARCADE": "INDUS",
    "DEPARTMENT_STORE": "INDUS",
    "NURSING_HOME": "INDUS",
    "CARPENTRY_SHOP": "INDUS",
    "BUTCHER": "INDUS",
    "GARAGE": "INDUS",
    "OFFICE": "INDUS",
    "HOSPITAL": "INDUS",
    "BAKERY": "INDUS",
    "MINI_GOLF_COURSE": "INDUS",
    "FUEL_STATION": "INDUS",
    "CAR_PARK": "INDUS",
    "DOUBLE_GARAGE": "PARK",
    "SINGLE_GARAGE": "PARK",
    "OPEN_SLOT": "PARK",
    "OUTDOOR_PARKING_PLACE_BIKE": "PARK",
    "BOAT_MOORING": "PARK",
    "BOAT_LANDING_STAGE": "PARK",
    "HORSE_BOX": "PARK",
    "COVERED_SLOT": "PARK",
    "BOAT_DRY_DOCK": "PARK",
    "UNDERGROUND_SLOT": "PARK",
    "COVERED_PARKING_PLACE_BIKE": "PARK",
    "COMMERCIAL_LAND": "PROP",
    "INDUSTRIAL_LAND": "PROP",
    "AGRICULTURAL_LAND": "PROP",
    "BUILDING_LAND": "PROP",
    "HOBBY_ROOM": "SECONDARY",
    "CELLAR_COMPARTMENT": "SECONDARY",
    "ATTIC_COMPARTMENT": "SECONDARY",
    "NA_MISC_0": "MISC",
    "NA_MISC_1": "MISC",
    "NA_MISC_2": "MISC",
    "NA_MISC_3": "MISC",
    "NA_MISC_4": "MISC",
    "NA_MISC_5": "MISC",
    "NA_MISC_6": "MISC",
    "NA_MISC_7": "MISC",
    "NA_AINVEST_2": "AINVEST",
    "NA_AINVEST_0": "AINVEST",
    "NA_PARK_0": "PARK",
    "NA_AGRI_0": "AGRI",
    "NA_APARTMENT_0": "APPT",
    "NA_INDUS_0": "INDUS",
    "NA_GASTRO_0": "GASTRO",
    "NA_PROP_0": "PROP",
    "NA_PARK_6": "PARK",
    "NA_HOUSE_0": "HOUSE",
    "HOUSE": "HOUSE",
    "EXHIBITION_SPACE": "INDUS",
    "BED_AND_BREAKFAST": "GASTRO",
    "BUNGALOW": "HOLI",
    "CAFE_BAR": "GASTRO",
    "PLOT": "PROP",
    "RETAIL": "INDUS",
    "WAREHOUSE": "INDUS",
    "RETAIL_SPACE": "INDUS",
    "ENGADINE_HOUSE": "HOUSE",
    "GARDEN_APARTMENT": "APPT",
    "HOME": "MISC",
    "HOUSE_PART": "HOUSE",
    "PATRICIAN_HOUSE": "HOUSE",
    "RUSTIC_HOUSE": "HOUSE",
    "MAISONETTE": "APPT",
    "FLAT": "APPT",
}


def get_category_code(category: Any) -> str:
    category = category.split(",")[0]
    category_code = category_to_code[category]
    return category_code


def load_pickle(path: str) -> Any:
    """
    Loads a pickle from a file at a given path.
    """
    with open(path, "rb") as pickle_file:
        return pickle.load(pickle_file)
