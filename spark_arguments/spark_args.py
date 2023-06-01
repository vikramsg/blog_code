from functools import partial
import random
from typing import Tuple

import numpy as np
import pandas as pd
import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql import SparkSession

_CATEGORIES = [0, 1, 2]  # ["red", "green", "blue"]
_YEARS = range(2010, 2021)
_X_VALUES = [0, 0.1, 0.25, 0.5, 1.0]
_INTERPOLATE_AT = 0.3


def _create_dataframe_data() -> pd.DataFrame:
    columns = ["category", "year", "x", "y"]
    data = []
    for category in _CATEGORIES:
        for year in _YEARS:
            for x in _X_VALUES:
                y = 25.0 * x + random.uniform(0, 1)
                data.append([category, year, x, y])
    return data, columns


def create_dataframe_pd() -> pd.DataFrame:
    data, columns = _create_dataframe_data()
    return pd.DataFrame(data, columns=columns)


def numpy_groupby_global_args(indices: Tuple[int, int], df: pd.DataFrame) -> pd.DataFrame:
    interpolated_value = np.interp(_INTERPOLATE_AT, df["x"], df["y"])

    return pd.DataFrame(
        data={
            "category": indices[0],
            "year": indices[1],
            "interpolated_value": interpolated_value,
        },
        index=[indices[0]],
    )


def numpy_groupby_local_args(indices: Tuple[int, int], df: pd.DataFrame, interpolate_at: float) -> pd.DataFrame:
    interpolated_value = np.interp(interpolate_at, df["x"], df["y"])

    return pd.DataFrame(
        data={
            "category": indices[0],
            "year": indices[1],
            "interpolated_value": interpolated_value,
        },
        index=[indices[0]],
    )


def _spark_session() -> SparkSession:
    return (
        SparkSession.builder.master("local")
        .appName("spark-args")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.default.parallelism", "1")
        .getOrCreate()
    )


if __name__ == "__main__":
    spark_session = _spark_session()
    spark_df = spark_session.createDataFrame(create_dataframe_pd())

    interpolated_schema = T.StructType(
        [
            T.StructField("category", T.ShortType(), True),
            T.StructField("year", T.ShortType(), True),
            T.StructField("interpolated_value", T.FloatType(), True),
        ]
    )
    interpolated_df_global_args = spark_df.groupBy(F.col("category"), F.col("year")).applyInPandas(
        numpy_groupby_global_args, schema=interpolated_schema
    )

    interpolated_df_global_args.show(truncate=False)

    numpy_groupby_interpolate_at = partial(numpy_groupby_local_args, interpolate_at=_INTERPOLATE_AT)
    interpolated_df = spark_df.groupBy(F.col("category"), F.col("year")).applyInPandas(
        numpy_groupby_interpolate_at, schema=interpolated_schema
    )

    interpolated_df.show(truncate=False)
