
pub mod model {
    enum Rank {
        R2, R3, R4, R5, R6, R7, R8, R9, R10,
        RJack, RQueen, RKing, RAce
    }
    enum Suit {
        Clubs,
        Hearts,
        Diamonds,
        Spades
    }
    struct Card {
        suit: Suit,
        rank: Rank
    }
    enum CellCard {
        Card(Card),
        Wild
    }
    struct Player {
        id: String,
        name: String,
        hand: Vec<Card>
    }
    struct Cell {
        card: CellCard,
        player: Option<Player>
    }
    struct Row {
        cells: Vec<Cell>
    }
    struct Board {
        rows: usize,
        columns: usize,
        cells: Vec<Row>
    }
}


#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        let result = 2 + 2;
        assert_eq!(result, 4);
    }
}
