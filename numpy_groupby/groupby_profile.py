import random
import pandas as pd

_CATEGORIES = ["red", "green", "blue"]
_YEARS = range(1990, 2021)
_X_VALUES = [0, 0.1, 0.25, 0.5, 1.0]


def create_dataframe() -> pd.DataFrame:
    data = []
    for category in _CATEGORIES:
        for year in _YEARS:
            for x in _X_VALUES:
                y = 25.0 * x + random.uniform(0, 1)
                data.append([category, year, x, y])

    return pd.DataFrame(data, columns=["category", "year", "x", "y"])


if __name__ == "__main__":
    df = create_dataframe()
    print(df)
