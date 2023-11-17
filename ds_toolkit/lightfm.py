import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_pipeline

from .recommendations_utils import isnull

__all__ = [
    "features_to_tags_pipeline_buy",
    "features_to_tags_pipeline_rent",
    "features_to_list_with_tags_pipeline",
]


class RentPriceTransformer(BaseEstimator, TransformerMixin):
    """
    Sets price to None if it is above 99th quantile for almost all categories.
    For APPT and HOUSE categories sets price to nan if it is above 30'000 and 60'000 respectively.
    Those prices are much higher than 99th quantile. It is done to avoid deleting too expensive listings from some expensive cantons and municipalities.
    """

    def __init__(self):
        pass

    def fit(self, _X, _y=None):
        return self

    def transform(self, X):
        for category in X["CATEGORY_CODE"].unique():
            if category == "APPT":
                X["PRICE"] = np.where(
                    (X["CATEGORY_CODE"] == category) & (X["PRICE"] > 30000),
                    None,
                    X["PRICE"],
                )
            elif category == "HOUSE":
                X["PRICE"] = np.where(
                    (X["CATEGORY_CODE"] == category) & (X["PRICE"] > 60000),
                    None,
                    X["PRICE"],
                )
            else:
                quantile_99 = X.loc[X["CATEGORY_CODE"] == category][
                    "PRICE"
                ].quantile(0.99)
                X["PRICE"] = np.where(
                    (X["CATEGORY_CODE"] == category)
                    & (X["PRICE"] > quantile_99),
                    None,
                    X["PRICE"],
                )
        return X


class BuyPriceTransformer(BaseEstimator, TransformerMixin):
    """
    Sets price to None if it is above 99th quantile for every category.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        for category in X["CATEGORY_CODE"].unique():
            quantile_99 = X.loc[X["CATEGORY_CODE"] == category][
                "PRICE"
            ].quantile(0.99)
            X["PRICE"] = np.where(
                (X["CATEGORY_CODE"] == category) & (X["PRICE"] > quantile_99),
                None,
                X["PRICE"],
            )
        return X


class RentSpaceTransformer(BaseEstimator, TransformerMixin):
    """
    Sets space to None if it is suspicious low (equals or lower than 1 sqm).
    Only PARK and INDUS DISPLAY_WINDOW categories are allowed to have such space.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        for category in X["CATEGORY_CODE"].unique():
            for sub_category in X["CATEGORIES"].unique():
                if category == "PARK" or (
                    category == "INDUS" and sub_category == "DISPLAY_WINDOW"
                ):
                    X["SPACE"] = X["SPACE"]
                else:
                    X["SPACE"] = np.where(
                        (X["CATEGORY_CODE"] == category)
                        & (X["CATEGORIES"] == sub_category)
                        & (X["SPACE"] <= 1),
                        None,
                        X["SPACE"],
                    )
        return X


class BuySpaceTransformer(BaseEstimator, TransformerMixin):
    """
    Sets space to None for some categories if it is suspicious high or low:
    - APPT space is not allowed to be > 1000 or <= 1
    - PARK space is not allowed to be > 100
    - GASTRO, HOUSE spaces are not allowed to be <= 1
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        for category in X["CATEGORY_CODE"].unique():
            if category == "APPT":
                X["SPACE"] = np.where(
                    ((X["CATEGORY_CODE"] == category) & (X["SPACE"] > 1000))
                    | ((X["CATEGORY_CODE"] == category) & (X["SPACE"] <= 1)),
                    None,
                    X["SPACE"],
                )
            elif category == "PARK":
                X["SPACE"] = np.where(
                    (X["CATEGORY_CODE"] == category) & (X["SPACE"] > 100),
                    None,
                    X["SPACE"],
                )
            elif category in ["GASTRO", "HOUSE"]:
                X["SPACE"] = np.where(
                    (X["CATEGORY_CODE"] == category) & (X["SPACE"] <= 1),
                    None,
                    X["SPACE"],
                )
            else:
                continue
        return X


class FloorTransformer(BaseEstimator, TransformerMixin):
    """
    Sets floor to None if it is suspiciously high.
    The highest building in Switzerland has 50 floors.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X["FLOOR"] = np.where(X["FLOOR"] >= 50, None, X["FLOOR"])
        return X


class YearTransformer(BaseEstimator, TransformerMixin):
    """
    Splits built year if it's available into 7 bins:
    ancient, 1901-1920, 1921-1940, 1941-1960, 1961-1980, 1981-2000, modern
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X["YEAR"] = np.where(
            X["YEARBUILT"] <= 1900,
            "ancient",
            np.where(
                X["YEARBUILT"] <= 1920,
                "1901-1920",
                np.where(
                    X["YEARBUILT"] <= 1940,
                    "1921-1940",
                    np.where(
                        X["YEARBUILT"] <= 1960,
                        "1941-1960",
                        np.where(
                            X["YEARBUILT"] <= 1980,
                            "1961-1980",
                            np.where(
                                X["YEARBUILT"] <= 2000,
                                "1981-2000",
                                np.where(
                                    X["YEARBUILT"] > 2000, "modern", None
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        X.drop(columns=["YEARBUILT"], inplace=True)
        return X


class FeaturesIntoTagsTransformer(BaseEstimator, TransformerMixin):
    """
    Transforms every feature of every listing from pandas DataFrame
    into a list of tags - tuples (listing_id, features_list).
    These tags are needed for the LightFM model and should be in the string format.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        results = X.to_dict(orient="records")
        listings_features = []
        for item in results:
            features_list = []
            listing_id = None
            for k, v in item.items():
                if k == "LISTING_ID":
                    listing_id = v
                elif isnull(v):
                    continue
                else:
                    features_list.append(f"{k}:{v}")
            row = (listing_id, features_list)
            listings_features.append(row)
        return listings_features


class TagsListTransformer(BaseEstimator, TransformerMixin):
    """
    Transforms all listing features from FeaturesIntoTagsTransformer
    into a set of unique listing features.
    This set is needed for the LightFM model.
    """

    def __init__(self):
        pass

    def fit(self, _X, _y=None):
        return self

    def transform(self, X):
        feature_set = []
        for item in X:
            for i in item[1]:
                feature_set.append(i)
        feature_set = list(set(feature_set))
        return feature_set


features_to_tags_pipeline_buy = make_pipeline(
    BuyPriceTransformer(),
    BuySpaceTransformer(),
    FloorTransformer(),
    YearTransformer(),
    FeaturesIntoTagsTransformer(),
)
"""
# Build transofrmation pipeline for BUY listings:
# - clean some data (see Transformers' docstrings)
# - transform features into tags
# - create a set with all unique feature tags
"""


features_to_tags_pipeline_rent = make_pipeline(
    RentPriceTransformer(),
    RentSpaceTransformer(),
    FloorTransformer(),
    YearTransformer(),
    FeaturesIntoTagsTransformer(),
)
"""
# Build transofrmation pipeline for RENT listings:
# - clean some data (see Transformers' docstrings)
# - transform features into tags
# - create a set with all unique feature tags
"""

features_to_list_with_tags_pipeline = make_pipeline(TagsListTransformer())
