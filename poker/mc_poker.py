import math
import random
from collections import Counter
import time


# --- Konfiguration (ændr her) ---
# Kort: rang (2–9, T, J, Q, K, A) + kulør — s=spar, h=hjerter, d=ruder, c=klør
HERO_CARDS = ["Ah", "Ks"]
NUM_OPPONENTS = 1
N_SAMPLES = 100000
# Kendte community-kort (0–5 stk.): flop/turn/river allerede lagt, eller tom liste = alle 5 trækkes tilfældigt.
# Eksempel flop: ["Ah", "7d", "2c"]  ·  tom [] = preflop-lignende (5 tilfældige board-kort pr. run).
BOARD_CARDS: list[str] = []
# --------------------------------

ranks = "23456789TJQKA"
suits = "shdc"
deck = [r + s for r in ranks for s in suits]

rank_value = {r: i + 2 for i, r in enumerate(ranks)}


def card_rank(card: str) -> int:
    return rank_value[card[0]]


def card_suit(card: str) -> str:
    return card[1]


# Til pænt print (Unicode) — s/h/d/c som i deck
_SUIT_SYMBOL = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}


def format_card_pretty(card: str) -> str:
    if len(card) < 2:
        return card
    rank, suit_ch = card[0], card[1]
    sym = _SUIT_SYMBOL.get(suit_ch, suit_ch)
    return f"{rank}{sym}"


def format_cards_pretty(cards: list[str]) -> str:
    return "  ".join(format_card_pretty(c.strip()) for c in cards)


def evaluate_7(cards):
    rs = [card_rank(c) for c in cards]
    ss = [card_suit(c) for c in cards]
    rc = Counter(rs)
    sc = Counter(ss)

    flush_suit = None
    for s, cnt in sc.items():
        if cnt >= 5:
            flush_suit = s
            break

    def straight_high(ranks_list):
        uniq = sorted(set(ranks_list), reverse=True)
        if 14 in uniq:
            uniq.append(1)
        run = 1
        for i in range(len(uniq) - 1):
            if uniq[i] - 1 == uniq[i + 1]:
                run += 1
                if run >= 5:
                    return uniq[i - 3]
            elif uniq[i] != uniq[i + 1]:
                run = 1
        return None

    if flush_suit is not None:
        flush_ranks = [card_rank(c) for c in cards if card_suit(c) == flush_suit]
        sf = straight_high(flush_ranks)
        if sf is not None:
            return (8, sf)

    rank_counts = sorted(rc.values(), reverse=True)

    if rank_counts[0] == 4:
        quad = max(r for r, c in rc.items() if c == 4)
        kicker = max(r for r, c in rc.items() if c != 4)
        return (7, quad, kicker)

    trips = sorted([r for r, c in rc.items() if c >= 3], reverse=True)
    pairs = sorted([r for r, c in rc.items() if c >= 2 and r not in trips], reverse=True)
    if trips:
        top_trip = trips[0]
        remaining_trips = trips[1:]
        if remaining_trips or pairs:
            second = remaining_trips[0] if remaining_trips else pairs[0]
            return (6, top_trip, second)

    if flush_suit is not None:
        flush_cards = sorted([card_rank(c) for c in cards if card_suit(c) == flush_suit], reverse=True)[:5]
        return (5, *flush_cards)

    st = straight_high(rs)
    if st is not None:
        return (4, st)

    if trips:
        top_trip = trips[0]
        kickers = sorted([r for r in rc.keys() if r != top_trip], reverse=True)[:2]
        return (3, top_trip, *kickers)

    pair_ranks = sorted([r for r, c in rc.items() if c >= 2], reverse=True)
    if len(pair_ranks) >= 2:
        high_pair, low_pair = pair_ranks[:2]
        kicker = max(r for r in rc.keys() if r not in (high_pair, low_pair))
        return (2, high_pair, low_pair, kicker)

    if len(pair_ranks) == 1:
        pair = pair_ranks[0]
        kickers = sorted([r for r in rc.keys() if r != pair], reverse=True)[:3]
        return (1, pair, *kickers)

    highs = sorted(rs, reverse=True)[:5]
    return (0, *highs)


def main() -> None:
    t0 = time.time()
    hero = [c.strip() for c in HERO_CARDS]
    if len(hero) != 2:
        raise ValueError("HERO_CARDS skal indeholde præcis to kort.")
    if len(set(hero)) != 2:
        raise ValueError("De to heltkort skal være forskellige.")
    for c in hero:
        if c not in deck:
            raise ValueError(f"Ugyldigt kort: {c!r}. Brug f.eks. 'Ah' for hjerter-es.")

    board_fixed = [c.strip() for c in BOARD_CARDS]
    if len(board_fixed) > 5:
        raise ValueError("BOARD_CARDS kan højst indeholde 5 kort.")
    if len(board_fixed) != len(set(board_fixed)):
        raise ValueError("BOARD_CARDS må ikke have dubletter.")
    for c in board_fixed:
        if c not in deck:
            raise ValueError(f"Ugyldigt board-kort: {c!r}.")
        if c in hero:
            raise ValueError(f"Board-kort {c!r} overlapper med heltens hånd.")

    n_board_fixed = len(board_fixed)
    n_board_random = 5 - n_board_fixed

    if NUM_OPPONENTS < 1:
        raise ValueError("NUM_OPPONENTS skal være mindst 1.")

    base_pool = [c for c in deck if c not in hero and c not in board_fixed]
    cards_needed = 2 * NUM_OPPONENTS + n_board_random
    if cards_needed > len(base_pool):
        raise ValueError(
            f"Træk kræver {cards_needed} kort (modstandere + {n_board_random} tilfældige board-kort), "
            f"men der er kun {len(base_pool)} tilbage efter helt og faste board-kort."
        )

    wins = 0
    tie_equity = 0.0
    losses = 0

    for _ in range(N_SAMPLES):
        draw = random.sample(base_pool, cards_needed)
        opponents = [draw[2 * i : 2 * i + 2] for i in range(NUM_OPPONENTS)]
        board_random = draw[2 * NUM_OPPONENTS :]
        board = board_fixed + board_random  # altid 5 community-kort i alt

        hero_score = evaluate_7(hero + board)
        opp_scores = [evaluate_7(o + board) for o in opponents]
        best = max([hero_score, *opp_scores])
        all_scores = [hero_score, *opp_scores]
        winner_count = sum(1 for s in all_scores if s == best)

        if hero_score == best:
            if winner_count == 1:
                wins += 1
            else:
                tie_equity += 1.0 / winner_count
        else:
            losses += 1

    t1 = time.time()

    equity = (wins + tie_equity) / N_SAMPLES
    margin = 1.0 / math.sqrt(N_SAMPLES)
    lo_ci = max(0.0, equity - margin)
    hi_ci = min(1.0, equity + margin)
    dt_ms = (t1 - t0) * 1000.0

    _print_results(
        hero=hero,
        board_fixed=board_fixed,
        n_board_random=n_board_random,
        num_opponents=NUM_OPPONENTS,
        n_samples=N_SAMPLES,
        wins=wins,
        tie_equity=tie_equity,
        losses=losses,
        equity=equity,
        lo_ci=lo_ci,
        hi_ci=hi_ci,
        dt_ms=dt_ms,
    )


def _print_results(
    *,
    hero: list[str],
    board_fixed: list[str],
    n_board_random: int,
    num_opponents: int,
    n_samples: int,
    wins: int,
    tie_equity: float,
    losses: int,
    equity: float,
    lo_ci: float,
    hi_ci: float,
    dt_ms: float,
) -> None:
    w = 56
    line = "=" * w

    def pct(x: float) -> str:
        return f"{100.0 * x:.4f} %"

    hero_s = format_cards_pretty(hero)
    if board_fixed:
        board_s = format_cards_pretty(board_fixed)
    else:
        board_s = "(ingen — alle 5 board-kort tilfældige pr. run)"

    print()
    print(line)
    print(" Monte Carlo — poker equity".ljust(w - 1))
    print(line)
    print(f"  Hero:              {hero_s}")
    print(f"  Board (fast):      {board_s}")
    print(f"  Tilfældige board:  {n_board_random} pr. run")
    print(f"  Modstandere:       {num_opponents}")
    print(f"  Samples:           {n_samples:,}")
    print("-" * w)
    print(f"  Sejre:             {wins:,}")
    print(f"  Uafgjort (andel):  {tie_equity:.4f}")
    print(f"  Tab:               {losses:,}")
    print("-" * w)
    print(f"  Equity:            {pct(equity)}")
    print(f"  95 % CI (±1/√N):   [{pct(lo_ci)}  …  {pct(hi_ci)}]")
    print("-" * w)
    print(f"  Køretid:           {dt_ms:.1f} ms")
    print(line)
    print()


if __name__ == "__main__":
    main()
