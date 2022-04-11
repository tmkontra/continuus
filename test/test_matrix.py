from lib.matrix import _find_sequences_meeting_condition, _distinct_sequences


if __name__ == "__main__":
    me = "1"
    you = "0"
    N = sequence_length = 5

    def render(input_matrix, coords_list):
        outrows = []
        for row in range(len(input_matrix)):
            outrows.append(["0" for char in range(len(input_matrix[row]))])
        matrix = outrows
        for coords in coords_list:
            for (r,c), _ in coords:
                matrix[r][c] = "1"
        matrix = ["".join(row) for row in matrix]
        return "\n".join(matrix) + "\n"

    def test(string_matrix, expected, win_count):
        matrix = string_matrix.strip().split()
        cond = lambda c: c == me
        found = set(_find_sequences_meeting_condition(matrix, N, cond))
        winner = _distinct_sequences(found, win_count)
        if winner:
            assert len(winner) == expected, len(winner)
        else:
            assert expected == 0, "expected winner, didn't find any"

    two_orthogonal = """
        0000000
        0111110
        0100000
        0100000
        0100000
        0100000
        0000000
        """

    test(two_orthogonal, 2, 2)

    three_diag = """
        0000000
        0111110
        0110000
        0101000
        0100100
        0100010
        0100000
        """
    test(three_diag, 3, 3)

    two_long = """
        0000000000
        0000000000 
        0111111111
        0000000000
        0000000000
        0000000000
        0000000000
        0000000000
        0000000000
        0000000000
        """  # 9-sequence, two 5-sequences share 1 cell
    test(two_long, 2, 2)

    not_quite_two = """
        0000000000
        0000000000
        0111111110
        0000000000
        0000000000
        0000000000
        """  # 8-sequence overlaps too much
    test(not_quite_two, 1, 2)
