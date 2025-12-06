from dataclasses import dataclass, field
from drafter import *
import random
from drafter.llm import LLMMessage, LLMResponse, call_gemini, set_gemini_server

set_gemini_server("https://drafter-gemini-proxy.akmani.workers.dev/")

set_site_information(
    author="akmani@udel.edu, jwtrout@udel.edu",
    description="""Blackjack against a computer dealer.""",
    sources=["ChatGPT, Copilot"],
    planning=[""],
    links=["https://github.com/UD-F25-CS1/honors-hackathon-2025-team-gurt/"]
)

hide_debug_information()
set_website_title("Your Website Title")
set_website_framed(False)

set_website_style("none")
set_website_title("Hen House Casino")
add_website_css("body", "display:flex; align-items:center; justify-content:center; min-height:100vh; padding:24px; background: radial-gradient(circle at 50% 30%, #052a08 0%, #031b06 40%, #000c03 100%), repeating-linear-gradient(45deg, rgba(0,0,0,0.03) 0px, rgba(0,0,0,0.03) 1px, transparent 1px, transparent 6px); color: #f3f2ec; font-family: 'Segoe UI', Tahoma, sans-serif; font-size:18px;")
add_website_css("body::after", "content:''; position:fixed; left:0; top:0; right:0; bottom:0; pointer-events:none; background-image: radial-gradient(rgba(0,0,0,0.02) 1px, transparent 1px); background-size: 6px 6px; opacity:0.6; mix-blend-mode: multiply;")
add_website_css(".drafter-page", "max-width: 900px; margin: 24px auto; padding: 28px; background: rgba(0,0,0,0.22); border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.6); text-align: center; overflow:auto; max-height: calc(100vh - 48px);")
add_website_css("h1, h2, .header", "color: #fff8dc; text-shadow: 0 2px 6px rgba(0,0,0,0.7);")
add_website_css("button", "background: linear-gradient(#ffd66b, #ffb84d); color: #200; border: none; padding: 10px 14px; border-radius: 8px; font-weight: 700; box-shadow: 0 4px 0 rgba(0,0,0,0.25); cursor: pointer;")
add_website_css("button:hover", "transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.35);")
add_website_css("table", "background: transparent; border-collapse: separate; border-spacing: 8px; margin: 0 auto;")
add_website_css("td", "padding: 6px; text-align: center;")
add_website_css("table img", "display: block; margin: 0 auto; height: auto; max-width: 100%;")
add_website_css(".caption, small", "color: #e6e6d8; font-size: 0.9em;")
set_website_framed(False)
hide_debug_information()



@dataclass
class Card:
    suit : str 
    rank : int 
    image : Image

@dataclass
class State:
    dealer_cards: list[Card] = field(default_factory=list)
    player_cards: list[Card] = field(default_factory=list)
    money : int = 1000
    bet_amount : int = 0
    poker_stage : str = ""
    
@dataclass
class Deck:
    cards : list[Card]

def dealer_inital_deal(deck: Deck, hand: list[Card]) -> None:
    """Deal one card from the deck to the dealer's hand."""
    hand.append(deck.cards.pop())
    hand.append(deck.cards.pop())

def deal_card(deck: Deck, hand: list[Card]) -> None:
    """Deal one card from the deck to the dealer or player's hand."""
    hand.append(deck.cards.pop(0))

def hand_value(hand: list[Card]) -> str:
    """Calculate and return the value of a blackjack hand."""
    value = 0
    aces = 0
    for card in hand:
        if card.rank >= 10:
            value += 10
        elif card.rank == 1:
            aces += 1
            value += 11  # Initially count Ace as 11
        else:
            value += card.rank
    # Adjust for Aces if value exceeds 21
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return str(value)

def shuffle_deck() -> Deck:
    """Create and return a shuffled 52-card Deck.
    Each Card.image is set to an Image pointing to the local
    `Cards` folder using the filename scheme the course provides.
    """
    suits = ["♠", "♥", "♦", "♣"]
    suit_names = {"♣": "Clubs", "♦": "Diamonds", "♥": "Hearts", "♠": "Spades"}

    def rank_label(r: int) -> str:
        if r == 1:
            return "A"
        if r == 11:
            return "J"
        if r == 12:
            return "Q"
        if r == 13:
            return "K"
        return str(r)

    cards: list[Card] = []
    for suit in suits:
        sname = suit_names[suit]
        for rank in range(1, 14):
            label = rank_label(rank)
            filename = f"card{sname}{label}.png"
            # Build full Windows path to the image file.
            path = rf"\Cards\{filename}"
            # Create a Drafter Image object; use modest display size.
            img = Image(path, 100, 150)
            cards.append(Card(suit=suit, rank=rank, image=img))

    random.shuffle(cards)
    return Deck(cards=cards)

@route
def index(state: State) -> Page:
    return Page(state, content=[
        Header("Welcome to Hen House Casino!"),
        "You have $" +  str(state.money),
        Button("Start Blackjack", place_bet),
        Button("Play Poker", poker_index)
    ])

@route
def place_bet(state: State) -> Page:
    if not state.money:
        return you_lost(state)
    state.dealer_cards = []
    state.player_cards = []
    deck = shuffle_deck()
    return Page(state, content=[
        f"You have ${state.money}. How much would you like to bet?",
        TextBox("bet_amount", "100"),
        Button("Place bet & start game", check_valid_bet)
    ])

@route
def you_lost(state: State) -> Page:
    return Page(state, content=[
        Header("You have run out of money! Game over."),
        Button("Restart Game", index)
    ])

@route
def check_valid_bet(state: State, bet_amount : str) -> Page:
    if bet_amount.isdigit():
        if int(bet_amount) <= state.money:
            state.bet_amount = int(bet_amount)
            state.money -= state.bet_amount
            return blackjack_start(state)
    return place_bet(state)
        

@route 
def blackjack_start(state: State) -> Page:
    #print(deck)
    dealer_inital_deal(deck, state.dealer_cards)
    deal_card(deck, state.player_cards)
    deal_card(deck, state.player_cards)
    if int(hand_value(state.player_cards)) == 21:
        state.money += int(state.bet_amount * 2.5)
        return Page(state, content=[
            Header("Blackjack! You win!"),
            "Dealer Hand: " + hand_value(state.dealer_cards),
            Table([[card.image for card in state.dealer_cards]]),
            "Your Hand: " + hand_value(state.player_cards),
            Table([[card.image for card in state.player_cards]]),
            "Your money: " + "$" + str(state.money),
            Button("Place another bet?", place_bet)
,
            Button("Play Poker?", index)
        ])
    return Page(state, content=[
        "Dealer Hand: " + hand_value(state.dealer_cards[0:1]),
        Table([[state.dealer_cards[0].image, Image("\Cards\cardBack1.png", 100, 150)]]),
        "Your Hand: " + hand_value(state.player_cards),
        Table([[card.image for card in state.player_cards]]),
        HorizontalRule(),
        Button("Hit", blackjack_hit),
        Button("Stand", blackjack_stand),
        "Your money: " + "$" + str(state.money),
        "Your bet: " + "$" + str(state.bet_amount)
    ])

@route 
def blackjack_hit(state: State) -> Page:
    deal_card(deck, state.player_cards)
    if int(hand_value(state.player_cards)) > 21:
        return Page(state, content=[
            Header("You busted! Dealer wins."),
            "Dealer Hand: " + hand_value(state.dealer_cards),
            Table([[card.image for card in state.dealer_cards]]),
            "Your Hand: " + hand_value(state.player_cards),
            Table([[card.image for card in state.player_cards]]),
            "Your money: " + "$" + str(state.money),
            Button("Place another bet?", place_bet)
,
            Button("Play Poker?", index)
        ])
    if int(hand_value(state.player_cards)) == 21:
        return Page(state, content=[
            "Dealer Hand: " + hand_value(state.dealer_cards[0:1]),
            Table([[state.dealer_cards[0].image, Image("\Cards\cardBack1.png", 100, 150)]]),
            "Your Hand: " + hand_value(state.player_cards),
            Table([[card.image for card in state.player_cards]]),
            HorizontalRule(),
            Button("Stand", blackjack_stand),
            "Your money: " + "$" + str(state.money),
            "Your bet: " + "$" + str(state.bet_amount)
    ])
    return Page(state, content=[
        "Dealer Hand: " + hand_value(state.dealer_cards[0:1]),
        Table([[state.dealer_cards[0].image, Image("\Cards\cardBack1.png", 100, 150)]]),
        "Your Hand: " + hand_value(state.player_cards),
        Table([[card.image for card in state.player_cards]]),
        HorizontalRule(),
        Button("Hit", blackjack_hit),
        Button("Stand", blackjack_stand),
        "Your money: " + "$" + str(state.money),
        "Your bet: " + "$" + str(state.bet_amount)
    ])

@route 
def blackjack_stand(state: State) -> Page:
    # Dealer draws cards until >= 16
    deck = shuffle_deck()  
    while int(hand_value(state.dealer_cards)) <= 16:
        deal_card(deck, state.dealer_cards)
    
    # Now determine winner and return final page
    player_val = int(hand_value(state.player_cards))
    dealer_val = int(hand_value(state.dealer_cards))
    
    if dealer_val > 21:
        result = "You win! Dealer busted."
        state.money += state.bet_amount * 2
    elif player_val > dealer_val:
        result = "You win!"
        state.money += state.bet_amount * 2
    elif dealer_val > player_val:
        result = "Dealer wins."
    elif dealer_val == player_val and len(state.dealer_cards) == 2:
        result = "Dealer wins with Blackjack!"
        state.money -= state.bet_amount
    else:
        result = "Push (tie)."
        state.money += state.bet_amount
    
    return Page(state, content=[
        Header(result),
        "Dealer Hand:" + hand_value(state.dealer_cards),
        Table([[card.image for card in state.dealer_cards]]),
        "Your Hand:" + hand_value(state.player_cards),
        Table([[card.image for card in state.player_cards]]),
        "Your money: " + "$" + str(state.money),
        Button("Play again?", place_bet)
,
        Button("Play Poker?", index)

    ])

# ---------------------
# Simple Texas Hold'em routes (student-friendly, simplified scoring)
# ---------------------

def rank_value(card: Card) -> int:
    """Return numeric rank for comparison. Ace high = 14."""
    if card.rank == 1:
        return 14
    return card.rank


def evaluate_hand(cards: list[Card]) -> tuple:
    """Evaluate a 5-7 card poker hand and return a comparable tuple.

    Returns (category, tiebreakers...) where higher tuple means better hand.
    Categories (high to low):
      8 = Straight Flush, 7 = Four of a Kind, 6 = Full House,
      5 = Flush, 4 = Straight, 3 = Three of a Kind,
      2 = Two Pair, 1 = One Pair, 0 = High Card
    """
    if not cards:
        return (0,)

    # Build rank counts and suit groups
    ranks = [rank_value(c) for c in cards]
    rank_counts: dict[int, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    suits: dict[str, list[int]] = {}
    for c in cards:
        suits.setdefault(c.suit, []).append(rank_value(c))

    # Check for flush (any suit with >=5 cards)
    flush_suit = None
    flush_ranks: list[int] = []
    for s, rs in suits.items():
        if len(rs) >= 5:
            flush_suit = s
            flush_ranks = sorted(rs, reverse=True)
            break

    # Check for straight (consider Ace as 1 as well)
    unique_ranks = set(ranks)
    if 14 in unique_ranks:
        unique_ranks.add(1)
    seq = sorted(unique_ranks)
    best_straight_high = 0
    cur_len = 0
    prev = None
    cur_high = 0
    for v in seq:
        if prev is None or v == prev + 1:
            cur_len += 1
            cur_high = v
        else:
            cur_len = 1
            cur_high = v
        if cur_len >= 5 and cur_high > best_straight_high:
            best_straight_high = cur_high
        prev = v

    # Straight flush: check straight within flush suit ranks
    best_sf_high = 0
    if flush_suit is not None:
        flush_set = set(flush_ranks)
        if 14 in flush_set:
            flush_set.add(1)
        seqf = sorted(flush_set)
        prev = None
        cur_len = 0
        cur_high = 0
        for v in seqf:
            if prev is None or v == prev + 1:
                cur_len += 1
                cur_high = v
            else:
                cur_len = 1
                cur_high = v
            if cur_len >= 5 and cur_high > best_sf_high:
                best_sf_high = cur_high
            prev = v

    # If the straight flush is Ace-high, it's a Royal Flush (top category)
    if best_sf_high == 14:
        return (9,)

    # Helper to get sorted ranks by count then rank
    # returns list of (count, rank) sorted by count desc then rank desc
    count_rank = sorted(((cnt, r) for r, cnt in rank_counts.items()), key=lambda x: (x[0], x[1]), reverse=True)

    # Straight flush
    if best_sf_high:
        return (8, best_sf_high)

    # Four of a kind
    for cnt, r in count_rank:
        if cnt == 4:
            # kicker is highest remaining rank
            kickers = sorted([rv for rv in ranks if rv != r], reverse=True)
            kicker = kickers[0] if kickers else 0
            return (7, r, kicker)

    # Full house (three + pair)
    three_ranks = [r for cnt, r in count_rank if cnt == 3]
    pair_ranks = [r for cnt, r in count_rank if cnt == 2]
    # Also a three can serve as a pair if multiple threes
    if len(three_ranks) >= 2:
        # use highest three as three, next as pair
        return (6, three_ranks[0], three_ranks[1])
    if three_ranks and pair_ranks:
        return (6, three_ranks[0], pair_ranks[0])

    # Flush
    if flush_suit is not None:
        return (5, ) + tuple(flush_ranks[:5])

    # Straight
    if best_straight_high:
        return (4, best_straight_high)

    # Three of a kind
    if three_ranks:
        three = three_ranks[0]
        kickers = sorted([rv for rv in ranks if rv != three], reverse=True)[:2]
        return (3, three) + tuple(kickers)

    # Two pair
    if len(pair_ranks) >= 2:
        high_pair, low_pair = pair_ranks[0], pair_ranks[1]
        kickers = sorted([rv for rv in ranks if rv != high_pair and rv != low_pair], reverse=True)
        kicker = kickers[0] if kickers else 0
        return (2, high_pair, low_pair, kicker)

    # One pair
    if len(pair_ranks) == 1:
        pair = pair_ranks[0]
        kickers = sorted([rv for rv in ranks if rv != pair], reverse=True)[:3]
        return (1, pair) + tuple(kickers)

    # High card
    high_cards = sorted(ranks, reverse=True)[:5]
    return (0, ) + tuple(high_cards)


def rank_label_simple(r: int) -> str:
    if r == 14:
        return "A"
    if r == 13:
        return "K"
    if r == 12:
        return "Q"
    if r == 11:
        return "J"
    return str(r)


def hand_name(score: tuple) -> str:
    """Convert an evaluate_hand tuple into a human-readable name."""
    if not score:
        return "No hand"
    cat = score[0]
    if cat == 9:
        return "Royal Flush"
    if cat == 8:
        return f"Straight Flush (high {rank_label_simple(score[1])})"
    if cat == 7:
        return f"Four of a Kind: {rank_label_simple(score[1])}s"
    if cat == 6:
        return f"Full House: {rank_label_simple(score[1])}s full of {rank_label_simple(score[2])}s"
    if cat == 5:
        ranks = ",".join(rank_label_simple(r) for r in score[1:])
        return f"Flush (top cards: {ranks})"
    if cat == 4:
        return f"Straight (high {rank_label_simple(score[1])})"
    if cat == 3:
        kickers = ",".join(rank_label_simple(r) for r in score[2:])
        return f"Three of a Kind: {rank_label_simple(score[1])}s; kickers {kickers}"
    if cat == 2:
        return f"Two Pair: {rank_label_simple(score[1])}s and {rank_label_simple(score[2])}s; kicker {rank_label_simple(score[3])}"
    if cat == 1:
        kickers = ",".join(rank_label_simple(r) for r in score[2:])
        return f"One Pair: {rank_label_simple(score[1])}s; kickers {kickers}"
    # High card
    ranks = ",".join(rank_label_simple(r) for r in score[1:])
    return f"High Card: {ranks}"


@route
def poker_index(state: State) -> Page:
    return Page(state, content=[
        Header("Texas Hold'em"),
        Text("To start playing you will need to pay $10"),
        HorizontalRule(),
        Button("Play Texas Hold'em", holdem_start),
        Button("Back to Blackjack", index)
    ])


@route
def holdem_start(state: State) -> Page:
    # initialize poker fields on state
    state.money -= 10
    state.poker_player = []
    state.poker_dealer = []
    state.poker_community = []
    state.poker_stage = "preflop"
    state.poker_pot = 0
    state.poker_current_bet = 0
    # create fresh deck and store in state
    state.poker_deck = shuffle_deck()

    # deal two hole cards to player and dealer
    deal_card(state.poker_deck, state.poker_player)
    deal_card(state.poker_deck, state.poker_dealer)
    deal_card(state.poker_deck, state.poker_player)
    deal_card(state.poker_deck, state.poker_dealer)

    return Page(state, content=[
        Header("Preflop - Place Your Bet"),
        "Dealer Cards:",
        Table([[Image(r"\Cards\cardBack1.png", 100, 150), Image(r"\Cards\cardBack1.png", 100, 150)]]),
        "Community Cards:",
        Table([[card.image for card in state.poker_community]]),
        "Your Cards:",
        Table([[card.image for card in state.poker_player]]),
        HorizontalRule(),
        "Your Balance: $" + str(state.money),
        TextBox("bet_amount", "10"),
        Button("Place Bet", holdem_place_bet),
        Button("Fold", poker_index)
    ])


@route
def holdem_place_bet(state: State, bet_amount: str) -> Page:
    # Parse and validate bet
    try:
        bet = int(bet_amount)
        if bet < 0 or bet > state.money:
            return Page(state, content=[
                Header("Invalid Bet"),
                "Please enter a bet between $0 and $" + str(state.money),
                TextBox("bet_amount", "10"),
                Button("Try Again", holdem_place_bet)
            ])
        # Deduct bet from player and add to pot (dealer matches)
        state.money -= bet
        state.poker_pot = bet * 2
        state.poker_current_bet = bet
        return holdem_flop(state)
    except ValueError:
        return Page(state, content=[
            Header("Invalid Bet"),
            "Please enter a valid number.",
            TextBox("bet_amount", "10"),
            Button("Try Again", holdem_place_bet)
        ])


@route
def holdem_flop(state: State) -> Page:
    # burn one (ignore), then deal 3 community cards
    if getattr(state, 'poker_deck', None) is None:
        state.poker_deck = shuffle_deck()
    # burn
    _ = state.poker_deck.cards.pop(0)
    for _ in range(3):
        deal_card(state.poker_deck, state.poker_community)
    state.poker_stage = "flop"

    return Page(state, content=[
        Header("Flop"),
        "Dealer Cards:",
        Table([[Image(r"\Cards\cardBack1.png", 100, 150), Image(r"\Cards\cardBack1.png", 100, 150)]]),
        "Community Cards:",
        Table([[card.image for card in state.poker_community]]),
        "Your Cards:",
        Table([[card.image for card in state.poker_player]]),
        HorizontalRule(),
        "Pot: $" + str(state.poker_pot),
        "Your Balance: $" + str(state.money),
        TextBox("bet_amount", str(state.poker_current_bet)),
        Button("Raise", holdem_raise_bet),
        Button("Check", holdem_turn),
        Button("Fold", poker_index)
    ])


@route
def holdem_raise_bet(state: State, bet_amount: str) -> Page:
    # Handle raise bet during flop/turn/river
    try:
        bet = int(bet_amount)
        if bet < 0 or bet > state.money:
            return Page(state, content=[
                Header("Invalid Bet"),
                "Please enter a bet between $0 and $" + str(state.money),
                TextBox("bet_amount", str(state.poker_current_bet)),
                Button("Try Again", holdem_raise_bet)
            ])
        # Deduct bet and add to pot
        state.money -= bet
        state.poker_pot += bet * 2
        state.poker_current_bet = bet
        # Return to the current street to continue
        if state.poker_stage == "flop":
            return holdem_turn(state)
        elif state.poker_stage == "turn":
            return holdem_river(state)
        else:
            return holdem_showdown(state)
    except ValueError:
        return Page(state, content=[
            Header("Invalid Bet"),
            "Please enter a valid number.",
            TextBox("bet_amount", str(state.poker_current_bet)),
            Button("Try Again", holdem_raise_bet)
        ])


@route
def holdem_turn(state: State) -> Page:
    if getattr(state, 'poker_deck', None) is None:
        state.poker_deck = shuffle_deck()
    # burn
    _ = state.poker_deck.cards.pop(0)
    deal_card(state.poker_deck, state.poker_community)
    state.poker_stage = "turn"

    return Page(state, content=[
        Header("Turn"),
        "Dealer Cards:",
        Table([[Image(r"\Cards\cardBack1.png", 100, 150), Image(r"\Cards\cardBack1.png", 100, 150)]]),
        "Community Cards:",
        Table([[card.image for card in state.poker_community]]),
        "Your Cards:",
        Table([[card.image for card in state.poker_player]]),
        HorizontalRule(),
        "Pot: $" + str(state.poker_pot),
        "Your Balance: $" + str(state.money),
        TextBox("bet_amount", str(state.poker_current_bet)),
        Button("Raise", holdem_raise_bet),
        Button("Check", holdem_river),
        Button("Fold", poker_index)
    ])


@route
def holdem_river(state: State) -> Page:
    if getattr(state, 'poker_deck', None) is None:
        state.poker_deck = shuffle_deck()
    # burn
    _ = state.poker_deck.cards.pop(0)
    deal_card(state.poker_deck, state.poker_community)
    state.poker_stage = "river"

    return Page(state, content=[
        Header("River"),
        "Dealer Cards:",
        Table([[Image(r"\Cards\cardBack1.png", 100, 150), Image(r"Cards\cardBack1.png", 100, 150)]]),
        "Community Cards:",
        Table([[card.image for card in state.poker_community]]),
        "Your Cards:",
        Table([[card.image for card in state.poker_player]]),
        HorizontalRule(),
        "Pot: $" + str(state.poker_pot),
        "Your Balance: $" + str(state.money),
        TextBox("bet_amount", str(state.poker_current_bet)),
        Button("Raise", holdem_raise_bet),
        Button("Check", holdem_showdown),
        Button("Fold", poker_index)
    ])


@route
def holdem_showdown(state: State) -> Page:
    # Reveal dealer and compute winner using simplified highest-card rule
    player_combined = state.poker_player + state.poker_community
    dealer_combined = state.poker_dealer + state.poker_community
    p_score = evaluate_hand(player_combined)
    d_score = evaluate_hand(dealer_combined)

    if p_score > d_score:
        result = "You win!"
        state.money += state.poker_pot
    elif p_score < d_score:
        result = "Dealer wins."
    else:
        result = "Tie (split pot)."
        state.money += state.poker_pot // 2

    return Page(state, content=[
        Header("Showdown"),
        "Dealer Cards:",
        Table([[card.image for card in state.poker_dealer]]),
        "Community Cards:",
        Table([[card.image for card in state.poker_community]]),
        "Your Cards:",
        Table([[card.image for card in state.poker_player]]),
        HorizontalRule(),
        Text("Result: " + result),
        Text("Your Hand: " + hand_name(p_score)),
        Text("Dealer Hand: " + hand_name(d_score)),
        "Your money: $" + str(state.money),
        Button("Play again?", holdem_start),
        Button("Back to Blackjack", index)
    ])




deck = shuffle_deck()
start_server()









