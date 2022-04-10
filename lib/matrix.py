def iterate_submatrix(matrix, t, l, N):
    '''yield the horizontals and diagonals of NxN subsection of matrix starting at t(op), l(eft) as N-tuples'''
    submat = [row[l:l + N] for row in matrix[t:t + N]]
    for r in submat:
        yield tuple(r)
    for c in range(0, N):
        yield tuple(r[c] for r in submat)
    yield tuple(submat[rc][rc] for rc in range(0, N))
    yield tuple(submat[rc][N - 1 - rc] for rc in range(0, N))


def all_submatrix(matrix, N):
    for i in range(len(matrix) - N):
        for j in range(len(matrix[0]) - N):
            yield from iterate_submatrix(matrix, i, j, N)