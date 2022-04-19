import std/options

type
  Suit = enum
    sSpades, sDiamonds, sHearts, sClubs

  Rank = enum
    rAce, r2, r3, r4, r5, r6, r7, r8, r9, r10, rJack, rQueen, rKing

  Card = object
    suit: Suit
    rank: Rank

  Player = object
    id: string

  CellCardKind = enum
    ccCard, ccWild

  CellCard = object
    case kind: CellCardKind
    of CellCardKind.ccCard:
      card: Card
    of CellCardKind.ccWild:
      nil

  Cell = object
    card: CellCard
    player: Option[Player]

  Board = object
    rows: int
    columns: int
    cells: seq[Cell]

proc DefaultBoard(): Board =
  let
    size: int = 10
    D = Suit.sDiamonds
    H = Suit.sHearts
    S = Suit.sSpades
    C = Suit.sClubs
    Q = Rank.rQueen
    K = Rank.rKing
    A = Rank.rAce
    T = r10
    suits: seq[Option[Suit]] = @[
      none(Suit), some(D), some(D), some(D), some(D), some(D), some(D), some(D), some(D), none(Suit),
      some(D), some(H), some(H), some(S), some(S), some(S), some(S), some(S), some(S), some(C),
      some(D), some(H), some(D), some(D), some(C), some(C), some(C), some(C), some(S), some(C),
      some(D), some(H), some(D), some(H), some(H), some(H), some(H), some(C), some(S), some(C),
      some(D), some(H), some(D), some(H), some(H), some(H), some(H), some(C), some(S), some(C),
      some(S), some(H), some(D), some(H), some(H), some(H), some(H), some(C), some(S), some(C),
      some(S), some(H), some(D), some(C), some(C), some(C), some(C), some(C), some(S), some(C),
      some(S), some(H), some(D), some(D), some(D), some(D), some(D), some(D), some(S), some(C),
      some(S), some(H), some(H), some(H), some(H), some(C), some(C), some(C), some(C), some(C),
      none(Suit), some(S), some(S), some(S), some(S), some(S), some(S), some(S), some(S), none(Suit),
    ]
    ranks = @[
      none(Rank), some(r6), some(r7), some(r8), some(r9), some(T), some(Q), some(K), some(A), none(Rank),
      some(r5), some(r3), some(r2), some(r2), some(r3), some(r4), some(r5), some(r6), some(r7), some(A),
      some(r4), some(r4), some(K), some(A), some(A), some(K), some(Q), some(T), some(r8), some(K),
      some(r3), some(r5), some(Q), some(Q), some(T), some(r9), some(r8), some(r9), some(r9), some(Q),
      some(r2), some(r6), some(T), some(K), some(r3), some(r2), some(r7), some(r8), some(T), some(T),
      some(A), some(r7), some(r9), some(A), some(r4), some(r5), some(r6), some(r7), some(Q), some(r9),
      some(K), some(r8), some(r8), some(r2), some(r3), some(r4), some(r5), some(r6), some(K), some(r8),
      some(Q), some(r9), some(r7), some(r6), some(r5), some(r4), some(r3), some(r2), some(A), some(r7),
      some(T), some(T), some(Q), some(K), some(A), some(r2), some(r3), some(r4), some(r5), some(r6),
      none(Rank), some(r9), some(r8), some(r7), some(r6), some(r5), some(r4), some(r3), some(r2), none(Rank),
    ]
  var cells: seq[Cell]
  for i, s in suits:
    let c = case s.isNone:
      of true:
        CellCard(kind: CellCardKind.ccWild)
      of false:
        let r = ranks[i]
        let c = Card(rank: r.get(), suit: s.get())
        CellCard(kind: CellCardKind.ccCard, card: c)
    cells.add(Cell(card: c, player: none(Player)))
  Board(rows: size, columns: size, cells: cells)

proc NewDeck(): seq[Card] =
  var cards: seq[Card]
  for rank in Rank:
    for suit in Suit:
      cards.add(Card(rank: rank, suit: suit))
  cards


assert len(NewDeck()) == 52