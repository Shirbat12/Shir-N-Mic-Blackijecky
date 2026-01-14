import struct

"""
Shared protocol definitions for the Blackijecky game.
All constants and packet formats are defined here.
"""

# ---------------- Network Configuration ----------------
UDP_PORT = 13122
BUFFER_SIZE = 1024
BROADCAST_IP = '<broadcast>'

UDP_TIMEOUT = 3
TCP_CONNECT_TIMEOUT = 5
TCP_RECV_TIMEOUT = 60

# ---------------- Dealer Rules ----------------
DEALER_STANDS_ON = 17

# ---------------- Protocol Constants ----------------
MAGIC_COOKIE = 0xabcddcba

MSG_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4

ACTION_HIT = "Hittt"
ACTION_STAND = "Stand"

RESULT_WIN = 0x3
RESULT_LOSS = 0x2
RESULT_TIE = 0x1
RESULT_PLAYING = 0x0

# ---------------- Struct Formats ----------------
STRUCT_OFFER = '!IBH32s'
STRUCT_REQUEST = '!IBB32s'
STRUCT_PAYLOAD_PLAYER = '!IB5s'
STRUCT_PAYLOAD_DEALER = '!IBBHB'


def format_string(text):
    encoded = text.encode('utf-8')
    return encoded[:32].ljust(32, b'\x00')


def decode_string(bytes_val):
    return bytes_val.decode('utf-8').rstrip('\x00')


def parse_card(rank, suit):
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    rank_names = {1: 'Ace', 11: 'Jack', 12: 'Queen', 13: 'King'}

    suit_name = suits[suit] if 0 <= suit <= 3 else "Unknown"
    rank_name = rank_names.get(rank, str(rank))

    if rank == 1:
        value = 11
    elif rank >= 10:
        value = 10
    else:
        value = rank

    return f"{rank_name} of {suit_name}", value
