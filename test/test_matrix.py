from lib import matrix

no_winner = """
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
"""

horiz = """
0000000000
0000000000
0000000000
0001111100
0000000000
0000000000
0000000000
0000000000
0000000000
0000000000
"""

vert = """
0000000000
0000000000
0000000000
0000100000
0000100000
0000100000
0000100000
0000100000
0000000000
0000000000
"""

diag = """
0000000000
0000000000
0000000000
0000000100
0000001000
0000010000
0000100000
0001000000
0000000000
0000000000
"""


def parse(instring: str):
    string = instring.strip()
    rows = string.split("\n")
    out = []
    for row in rows:
        r = []
        for char in row:
            r.append(int(char))
        out.append(r)
    return out


SEQ_LENGTH = 5

if __name__ == "__main__":
    def test(chars):
        return any(all(seq) for seq in matrix.all_submatrix(parse(chars), SEQ_LENGTH))
    assert not test(no_winner)
    assert test(vert)
    assert test(horiz)
    assert test(diag)
