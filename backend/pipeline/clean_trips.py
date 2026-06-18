import numpy as np
import pandas as pd
from pipeline import config as C
from pipeline.transparency_log import TransparencyLog

RAW_COLS = {
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "VendorID": "vendor_id", 
    "RatecodeID": "rate_code_id",
    "PULocationID": "pu_location_id", 
    "DOLocationID": "do_location_id",
    "payment_type": "payment_type_id",
}


def clean(dataframe: pd.DataFrame, borough_by_zone: dict[int, str], transparency_log: TransparencyLog) -> pd.DataFrame:
    transparency_log.total_in += len(dataframe)
    dataframe = dataframe.rename(columns=RAW_COLS)

    # timestamps
    for col in ("pickup_datetime", "dropoff_datetime"):
        dataframe[col] = pd.to_datetime(dataframe[col], errors="coerce")

    bad_timestamp = dataframe["pickup_datetime"].isna() | dataframe["dropoff_datetime"].isna()
    transparency_log.drop("null_or_unparseable_timestamp", bad_timestamp.sum()); dataframe = dataframe[~bad_timestamp]

    # duration and ordering
    duration = (dataframe["dropoff_datetime"] - dataframe["pickup_datetime"]).dt.total_seconds()
    bad_duration = (duration < C.MIN_DURATION_SEC) | (duration > C.MAX_DURATION_SEC)

    transparency_log.drop("duration_out_of_range", bad_duration.sum()); dataframe, duration = dataframe[~bad_duration], duration[~bad_duration]
    dataframe["trip_duration_sec"] = duration.astype("int64")

    # distance and speed
    bad_distance = (dataframe["trip_distance"] <= 0) | (dataframe["trip_distance"] > C.MAX_TRIP_DISTANCE_MI)
    transparency_log.drop("distance_out_of_range", bad_distance.sum()); dataframe = dataframe[~bad_distance]

    dataframe["avg_speed_mph"] = dataframe["trip_distance"] / (dataframe["trip_duration_sec"] / 3600.0)
    bad_speed = dataframe["avg_speed_mph"] > C.MAX_SPEED_MPH
    transparency_log.drop("implausible_speed", bad_speed.sum()); dataframe = dataframe[~bad_speed]

    # fares
    bad_fare = (dataframe["fare_amount"] < 0) | (dataframe["fare_amount"] > C.MAX_FARE)
    transparency_log.drop("fare_out_of_range", bad_fare.sum()); dataframe = dataframe[~bad_fare]

    # deduplication
    before = len(dataframe); dataframe = dataframe.drop_duplicates()
    transparency_log.drop("exact_duplicate", before - len(dataframe))

    # built features
    dataframe["fare_per_mile"] = (dataframe["fare_amount"] / dataframe["trip_distance"]).replace([np.inf, -np.inf], np.nan)
    dataframe["tip_pct"] = np.where(dataframe["payment_type_id"] == 1,
                             dataframe["tip_amount"] / dataframe["fare_amount"].replace(0, np.nan) * 100, np.nan)
    dataframe["pickup_hour"] = dataframe["pickup_datetime"].dt.hour
    dataframe["pickup_dow"] = dataframe["pickup_datetime"].dt.dayofweek
    dataframe["is_weekend"] = dataframe["pickup_dow"] >= 5
    pu_b = dataframe["pu_location_id"].map(borough_by_zone)
    do_b = dataframe["do_location_id"].map(borough_by_zone)
    dataframe["is_inter_borough"] = (pu_b != do_b) & pu_b.notna() & do_b.notna()
    dataframe["store_and_fwd_flag"] = dataframe.get("store_and_fwd_flag", "N").map({"Y": True, "N": False})

    # Bound tip_pct: values outside [0, MAX_TIP_PCT] come from near-zero fares
    bad_tip = dataframe["tip_pct"].notna() & ((dataframe["tip_pct"] < 0) | (dataframe["tip_pct"] > C.MAX_TIP_PCT))
    transparency_log.note_null("implausible_tip_pct", int(bad_tip.sum()))
    dataframe.loc[bad_tip, "tip_pct"] = np.nan

    # Null categorical codes outside the seeded domain 
    from pipeline.seed_dims import VENDORS, RATE_CODES, PAYMENT_TYPES
    for col, valid in (("vendor_id", VENDORS), ("rate_code_id", RATE_CODES),
                       ("payment_type_id", PAYMENT_TYPES)):
        bad = dataframe[col].notna() & ~dataframe[col].isin(valid.keys())
        transparency_log.note_null(f"unknown_{col}", int(bad.sum()))
        dataframe.loc[bad, col] = None

    transparency_log.total_out += len(dataframe)
    return dataframe
