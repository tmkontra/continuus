import itertools
from typing import Tuple, Iterator, Callable, List, Sequence, Set

from lib.model import Cell

Coordinate = Tuple[int, int]
SubCell = Tuple[Coordinate, Cell]
CSequence = Sequence[SubCell]  # Cell Sequence
MultiSequence = Iterator[CSequence]
Matrix = List[List[Cell]]
CellCondition = Callable[[Cell], bool]


def get_valid_sequences(board: Matrix, sequence_length: int, cell_condition: CellCondition, win_count: int):
    seqs = _find_sequences_meeting_condition(board, sequence_length, cell_condition)
    distinct = _distinct_sequences(seqs, win_count)
    return distinct

def _find_sequences_meeting_condition(grid, sequence_length: int, cell_condition: CellCondition) -> MultiSequence:
    for sequence in _all_submatrices(grid, sequence_length):
        if all(cell_condition(cell[1]) for cell in sequence):
            yield sequence


def _distinct_sequences(sequences: Set[CSequence], required: int):
    max_group_size = min(len(sequences), required)
    for group_size in reversed(range(max_group_size+1)):
        for group in itertools.combinations(sequences, group_size):
            if _check_distinct(group):  # noqa
                return group


def _all_submatrices(matrix: Matrix, sequence_length: int) -> MultiSequence:
    for start_row in range(len(matrix) + 1 - sequence_length):
        for start_column in range(len(matrix[0]) + 1 - sequence_length):
            yield from _iterate_submatrix(matrix, start_row, start_column, sequence_length)


def _iterate_submatrix(matrix: Matrix, start_row: int, start_column: int, N: int) -> MultiSequence:
    """Yield the horizontals and diagonals of NxN subsection of matrix starting at start_row, start_column as N-tuples.
    (0,0) is top left
    Return type is a 2-tuple of (coordinate, cell) giving the absolute position of the cell in the greater matrix
    :return generator of `SubCell` sequences
    """
    submatrix = [row[start_column:start_column + N] for row in matrix[start_row:start_row + N]]
    # yield rows
    for r, row in enumerate(submatrix):
        yield tuple(((start_row + r, start_column + c), cell) for c, cell in enumerate(row))
    # yield columns
    for column_index in range(0, N):
        yield tuple((((start_row + r, start_column + column_index), row[column_index])
                     for r, row in enumerate(submatrix)))
    # yield diagonal down-to-right
    yield tuple(((start_row + diag, start_column + diag), submatrix[diag][diag]) for diag in range(0, N))
    # yield diagonal up-to-right
    yield tuple(((start_row + diag_rev, start_column + (N - 1 - diag_rev)), submatrix[diag_rev][N - 1 - diag_rev])
                for diag_rev in range(0, N))


def _coords_from_sequence(sequence: CSequence) -> Set[Coordinate]:
    return set(coord for (coord, _) in sequence)


def _check_pair_distinct(first, second) -> bool:
    return len(_coords_from_sequence(first).intersection(_coords_from_sequence(second))) <= 1


def _check_distinct(sequence_group: List[CSequence]) -> bool:
    for pair in itertools.combinations(sequence_group, 2):
        if not _check_pair_distinct(pair[0], pair[1]):
            return False
    return True



