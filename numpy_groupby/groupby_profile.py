import random
import timeit

import numpy as np
import pandas as pd

_CATEGORIES = ["red", "green", "blue"]
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


def _interpolate_wrapper(fp: np.ndarray, xp: np.ndarray, x: float) -> float:
    return float(np.interp(x=x, xp=xp, fp=fp))


def numpy_groupby(df: pd.DataFrame) -> pd.DataFrame:
    categories = df["category"].to_numpy()
    years = df["year"].to_numpy()
    x_values = df["x"].to_numpy()
    y_values = df["y"].to_numpy()

    x_unique_values = np.unique(x_values)
    num_x_unique_values = len(x_unique_values)

    sort_indices = np.lexsort((x_values, years, categories))
    y_values = y_values[sort_indices]

    y_values = y_values.reshape([-1, num_x_unique_values])
    interpolated_y_values = np.apply_along_axis(
        _interpolate_wrapper,
        axis=1,
        arr=y_values,
        x=_INTERPOLATE_AT,
        xp=x_unique_values,
    )

    return pd.DataFrame(
        data={
            "category": categories.reshape([-1, num_x_unique_values])[:, 0],
            "year": years.reshape([-1, num_x_unique_values])[:, 0],
            "y": interpolated_y_values,
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
    numpy_times = timeit.repeat(
        "numpy_groupby(df)",
        "from __main__ import create_dataframe, numpy_groupby;df = create_dataframe();",
        number=100,
    )
    print(f"Numpy times: {numpy_times}")
    pandas_times = timeit.repeat(
        "pandas_groupby(df)",
        "from __main__ import create_dataframe, pandas_groupby;df = create_dataframe()",
        number=100,
    )
    print(f"Pandas times: {pandas_times}")
