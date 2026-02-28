"""
KAN-59: Sort the given matrix then update it.

Given a matrix (2D list), sort all elements in ascending order and update the matrix
by filling row-wise with the sorted values. O(n log n) for sort, O(m*n) space for flat copy.
"""

from typing import List


def sort_matrix_and_update(matrix: List[List[int]]) -> List[List[int]]:
    """
    Sort all elements of the matrix and update it row-wise with sorted values.
    Does not mutate the original; returns a new matrix (caller can assign back if desired).

    Example:
        [[3, 1, 2], [6, 5, 4]] -> [[1, 2, 3], [4, 5, 6]]
    """
    if not matrix or not matrix[0]:
        return matrix if matrix else []
    rows, cols = len(matrix), len(matrix[0])
    flat = [matrix[i][j] for i in range(rows) for j in range(cols)]
    flat.sort()
    out = []
    idx = 0
    for _ in range(rows):
        out.append(flat[idx : idx + cols])
        idx += cols
    return out


if __name__ == "__main__":
    m1 = [[3, 1, 2], [6, 5, 4]]
    assert sort_matrix_and_update(m1) == [[1, 2, 3], [4, 5, 6]]
    assert sort_matrix_and_update([]) == []
    assert sort_matrix_and_update([[1]]) == [[1]]
    assert sort_matrix_and_update([[2], [1]]) == [[1], [2]]
    print("All tests passed.")
