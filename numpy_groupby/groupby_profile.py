import random
import timeit

import numba as nb
import numpy as np
import pandas as pd

from lexsort_array import lexsort

_CATEGORIES = [0, 1, 2]  # ["red", "green", "blue"]
_YEARS = range(2010, 2021)
_X_VALUES = [0, 0.1, 0.25, 0.5, 1.0]
_INTERPOLATE_AT = 0.3


def create_dataframe() -> pd.DataFrame:
    data = []
    for category in _CATEGORIES:
        for year in _YEARS:
            for x in _X_VALUES:
                y = 25.0 * x + random.uniform(0, 1)
                data.append([category, year, x, y])

    return pd.DataFrame(data, columns=["category", "year", "x", "y"])


@nb.njit
def _interpolate_wrapper(fp: np.ndarray, xp: np.ndarray, x: float) -> float:
    return float(np.interp(x=x, xp=xp, fp=fp))


@nb.njit
def _groupby_interpolate(
    categories: np.ndarray,
    years: np.ndarray,
    x_values: np.ndarray,
    y_values: np.ndarray,
) -> np.ndarray:
    x_unique_values = np.unique(x_values)
    num_x_unique_values = len(x_unique_values)

    sort_indices = lexsort((x_values, years, categories))
    y_values = y_values[sort_indices]

    reshape_y_size = np.int64(num_x_unique_values)
    reshape_x_size = np.int64(len(y_values) / reshape_y_size)

    # This is the only format for which reshape works with Numba
    # Uniform data type and no tuple/list as argument
    y_values = y_values.reshape(reshape_x_size, reshape_y_size)

    interpolate_values = np.zeros(reshape_x_size)
    for i in range(reshape_x_size):
        interpolate_values[i] = np.interp(
            x=_INTERPOLATE_AT, xp=x_unique_values, fp=y_values[i, :]
        )
    return interpolate_values


def numpy_groupby(df: pd.DataFrame) -> pd.DataFrame:
    categories = df["category"].to_numpy()
    years = df["year"].to_numpy()
    x_values = df["x"].to_numpy()
    y_values = df["y"].to_numpy()

    x_unique_values = np.unique(x_values)
    num_x_unique_values = len(x_unique_values)

    return pd.DataFrame(
        data={
            "category": categories.reshape([-1, num_x_unique_values])[:, 0],
            "year": years.reshape([-1, num_x_unique_values])[:, 0],
            "y": _groupby_interpolate(categories, years, x_values, y_values),
        }
    )


def pandas_groupby(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["category", "year"])
        .apply(lambda df: np.interp(_INTERPOLATE_AT, df["x"], df["y"]))
        .rename("y")
        .reset_index()
    )


if __name__ == "__main__":
    pandas_times = timeit.repeat(
        "pandas_groupby(df)",
        "from __main__ import create_dataframe, pandas_groupby;df = create_dataframe()",
        number=100,
    )
    print(f"Pandas times: {pandas_times}")
    numpy_times = timeit.repeat(
        "numpy_groupby(df)",
        "from __main__ import create_dataframe, numpy_groupby;df = create_dataframe();",
        number=100,
    )
    print(f"Numpy times: {numpy_times}")
