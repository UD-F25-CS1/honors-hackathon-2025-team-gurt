from dataclasses import dataclass, field
from drafter import *
import random
import time

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
    state.money = 1000
    return Page(state, content=[
        Header("Welcome to Hen House Blackjack!"),
        "You will start with " +  str(bold("$1,000")),
        Button("Start Blackjack", place_bet)

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
    ])


deck = shuffle_deck()
start_server()








