# https://github.com/numba/numba/issues/5688

from numba import njit, literal_unroll
import numpy as np


@njit
def cmp_fn(left, right, *arrays):
    for a in literal_unroll(arrays):
        if a[left] < a[right]:
            return -1  # less than
        elif a[left] > a[right]:
            return 1  # greater than

    return 0  # equal


@njit
def quicksort(index, Left, Right, *arrays):
    left, right = Left, Right
    pivot = index[(left + right) // 2]

    while True:
        while left < Right and cmp_fn(index[left], pivot, *arrays) == -1:
            left += 1
        while right >= Left and cmp_fn(pivot, index[right], *arrays) == -1:
            right -= 1

        if left >= right:
            break

        index[left], index[right] = index[right], index[left]
        left += 1
        right -= 1

        if Left < right:
            quicksort(index, Left, right, *arrays)

        if left < Right:
            quicksort(index, left, Right, *arrays)


@njit(nogil=True, cache=True, debug=True)
def lexsort(arrays):
    # print("starting lexsort")

    if len(arrays) == 0:
        return np.empty((), dtype=np.intp)

    if len(arrays) == 1:
        return np.argsort(arrays[0])

    for a in literal_unroll(arrays[1:]):
        if a.shape != arrays[0].shape:
            raise ValueError("lexsort array shapes don't match")

    n = arrays[0].shape[0]
    index = np.arange(n)

    quicksort(index, 0, n - 1, *arrays)

    # print("ending lexsort")
    return index


# a = np.array([2, 1, 4, 3, 0], dtype=np.int32)
# b = np.array([1, 2, 3, 4, 5], dtype=np.float64)
#
# print("before lexsort")
# print(lexsort((a, b)))
# print("after lexsort")
