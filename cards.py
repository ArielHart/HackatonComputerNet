"""Deck and scoring for simplified blackjack."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple

# Wire encoding:
# - rank: 1..13 (A=1, J=11, Q=12, K=13)
# - suit: 0..3 (H,D,C,S)

SUIT_NAMES = ("Heart", "Diamond", "Club", "Spade")
RANK_NAMES = {
    1: "A",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "10",
    11: "J",
    12: "Q",
    13: "K",
}

def rank_value(rank: int) -> int:
    if rank == 1:
        return 11  # Ace fixed to 11 in this assignment
    if 2 <= rank <= 10:
        return rank
    return 10  # J,Q,K

@dataclass(frozen=True)
class Card:
    rank: int
    suit: int

    def value(self) -> int:
        return rank_value(self.rank)

    def short(self) -> str:
        return f"{RANK_NAMES.get(self.rank, str(self.rank))}{'HDCS'[self.suit]}"

    def pretty(self) -> str:
        return f"{RANK_NAMES.get(self.rank, str(self.rank))} of {SUIT_NAMES[self.suit]}"

class Deck:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._cards: List[Card] = [
            Card(rank=r, suit=s)
            for s in range(4)
            for r in range(1, 14)
        ]
        self._rng.shuffle(self._cards)

    def draw(self) -> Card:
        if not self._cards:
            raise RuntimeError("deck is empty")
        return self._cards.pop()

def hand_total(hand: List[Card]) -> int:
    return sum(c.value() for c in hand)
