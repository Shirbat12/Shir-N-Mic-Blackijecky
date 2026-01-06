import struct

"""
Protocol definition for Blackijecky. Shared constants and packet formats.
"""

# Network Constants
UDP_PORT = 13122  # Fixed UDP port for offers 
BUFFER_SIZE = 1024  # Standard buffer size
BROADCAST_IP = '<broadcast>'

# Protocol Constants
MAGIC_COOKIE = 0xabcddcba  # Start of every packet 

# Message Types
MSG_TYPE_OFFER = 0x2  # Dealer -> Player (UDP)
MSG_TYPE_REQUEST = 0x3  # Player -> Dealer (TCP) 
MSG_TYPE_PAYLOAD = 0x4  # Game moves (TCP) 

# Game Actions (Player -> Dealer)
# Must be exactly 5 bytes 
ACTION_HIT = "Hittt"
ACTION_STAND = "Stand"

# Game Results (Dealer -> Player) 
RESULT_WIN = 0x3
RESULT_LOSS = 0x2
RESULT_TIE = 0x1
RESULT_PLAYING = 0x0  # Round is still ongoing

# Struct Formats (Big Endian '!')
# I=4 bytes, H=2 bytes, B=1 byte, s=string

# Offer: Cookie(4), Type(1), ServerPort(2), ServerName(32) 
STRUCT_OFFER = '!IBH32s' 

# Request: Cookie(4), Type(1), Rounds(1), TeamName(32) 
STRUCT_REQUEST = '!IBB32s'

# Player Payload: Cookie(4), Type(1), Decision(5 bytes)
STRUCT_PAYLOAD_PLAYER = '!IB5s'

# Dealer Payload: Cookie(4), Type(1), Result(1), Rank(2), Suit(1) 
STRUCT_PAYLOAD_DEALER = '!IBBHB'


# Helper Functions

def format_string(string_val):
    """Pads string to exactly 32 bytes with nulls."""
    encoded = string_val.encode('utf-8')
    if len(encoded) < 32:
        return encoded + b'\x00' * (32 - len(encoded))
    return encoded[:32]

def decode_string(bytes_val):
    """Decodes string and removes null padding."""
    return bytes_val.decode('utf-8').rstrip('\x00')

def parse_card(rank, suit):
    """Converts card numbers to readable text and game value."""
    # Suit mapping: 0=Hearts, 1=Diamonds, 2=Clubs, 3=Spades
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    suit_name = suits[suit] if 0 <= suit <= 3 else "Unknown"
    
    # Rank mapping 
    rank_names = {1: 'Ace', 11: 'Jack', 12: 'Queen', 13: 'King'}
    rank_name = rank_names.get(rank, str(rank))
    
    # Game Value Calculation 
    if rank == 1:
        value = 11  # Ace starts as 11
    elif rank >= 10:
        value = 10
    else:
        value = rank
        
    display_str = f"{rank_name} of {suit_name}"
    return display_str, value