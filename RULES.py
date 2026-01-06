import struct

"""
Protocol definition for Blackijecky Hackathon.
This file is shared between server and client to ensure strict compliance
with the packet formats and to avoid code duplication.
"""

# --- Network Constants ---
# Default port for UDP Broadcast.
# NOTE: Source 114 claims 13122, but Source 124 code example uses 13117.
# We adhere to 13122 to match the text.
UDP_PORT = 13122
BUFFER_SIZE = 1024
BROADCAST_IP = '<broadcast>'

# --- Magic Cookie ---
# Source 87: All messages must start with this cookie.
MAGIC_COOKIE = 0xabcddcba

# --- Message Types ---
OFFER = 0x2    # Server -> Client (UDP) [cite: 88]
REQUEST = 0x3  # Client -> Server (TCP) [cite: 93]
PAYLOAD = 0x4  # Game move/result (TCP) [cite: 99]

# --- Game Constants ---
# Player decisions - Source 100 requires strict 5 bytes.
# "Hit" is too short, so it must be "Hittt".
HIT = "Hittt"
STAND = "Stand"

# Game Results [cite: 101]
WIN = 0x3
LOSS = 0x2
TIE = 0x1
PLAY = 0x0  # Continue playing

# --- Packet Formats (Structs) ---
# We use '!' for Network Byte Order (Big Endian) to ensure cross-platform compatibility.
# Format codes: I=4 bytes (int), H=2 bytes (short), B=1 byte, s=string (char)

# Offer Message: Cookie (4), Type (1), Server Port (2), Server Name (32)
# [cite: 85-90]
OFFER_MSG_STRUCT = '!IBH32s'

# Request Message: Cookie (4), Type (1), Rounds (1), Team Name (32)
# Source 94 specifies Rounds is 1 byte. [cite: 91-95]
REQUEST_MSG_STRUCT = '!IBB32s'

# Payload (Client -> Server): Cookie (4), Type (1), Decision (5 bytes string)
# 
PAYLOAD_CLIENT_MSG_STRUCT = '!IB5s'

# Payload (Server -> Client): Cookie (4), Type (1), Result (1), Card Rank (2), Card Suit (1)
# Note: Card is 3 bytes total. Rank is 2 bytes, Suit is 1 byte. [cite: 102-103]
PAYLOAD_SERVER_MSG_STRUCT = '!IBBHB'


# --- Helper Functions ---

def format_string(string_val):
    """
    Helper to ensure strings are exactly 32 bytes:
    - Encodes to UTF-8
    - Pads with null bytes (\x00) if too short
    - Truncates if too long
    Required for Server Name and Team Name fields.
    """
    encoded = string_val.encode('utf-8')
    if len(encoded) < 32:
        return encoded + b'\x00' * (32 - len(encoded))
    return encoded[:32]

def decode_string(bytes_val):
    """
    Helper to decode 32-byte strings, removing null padding.
    """
    return bytes_val.decode('utf-8').rstrip('\x00')

def parse_card(card_val, suit):
    """
    Translates raw card data to readable string/value.
    Rank: 1-13
    Suit: 0-3 (Hearts, Diamonds, Clubs, Spades - HDCS order [cite: 103])
    """
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    value_names = {1: 'Ace', 11: 'Jack', 12: 'Queen', 13: 'King'}

    # Logic for value calculation (10 for face cards, 11 for Ace initially)
    if card_val == 1:
        value = 11
    elif card_val >= 10:
        value = 10
    else:
        value = card_val

    name = value_names.get(card_val, str(card_val))
    suit_name = suits[suit] if 0 <= suit <= 3 else "Unknown"

    return f"{name} of {suit_name}", value