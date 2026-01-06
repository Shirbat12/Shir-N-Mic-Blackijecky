import socket
import time
import threading
import random
import struct
import RULES

class Dealer:
    def __init__(self):
        self.team_name = "BlackjackDealer"
        self.tcp_port = 0   # OS will assign a free port
        self.server_ip = self.get_local_ip()
        self.running = True
        
        # Initialize Sockets
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(('', 0))  # bind to ephemeral port
        self.tcp_port = self.tcp_socket.getsockname()[1]
        self.tcp_socket.listen(5)
        
        print(f"Dealer started, listening on IP address {self.server_ip}") 

    def get_local_ip(self):
        """Finds the actual local IP address (not 127.0.0.1)."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        # 1. Start UDP Broadcast in background
        threading.Thread(target=self.broadcast_offers, daemon=True).start()
        
        # 2. Main loop: Accept TCP connections
        while self.running:
            try:
                client_conn, addr = self.tcp_socket.accept()
                print(f"New connection from {addr}")
                # Handle player in separate thread
                threading.Thread(target=self.handle_player, args=(client_conn,)).start()
            except Exception as e:
                print(f"Accept error: {e}")

    def broadcast_offers(self):
        """Broadcasts Offer packet every 1 second."""
        packet = struct.pack(
            rules.STRUCT_OFFER,
            rules.MAGIC_COOKIE,
            rules.MSG_TYPE_OFFER,
            self.tcp_port,
            rules.format_string(self.team_name)
        )
        
        while self.running:
            try:
                self.udp_socket.sendto(packet, (rules.BROADCAST_IP, rules.UDP_PORT))
                time.sleep(1) 
            except Exception as e:
                print(f"Broadcast failed: {e}")

    def handle_player(self, conn):
        """Handles a single player game session."""
        try:
            # Receive Request
            data = conn.recv(rules.BUFFER_SIZE)
            if not data: return
            
            cookie, msg_type, rounds, name_bytes = struct.unpack(rules.STRUCT_REQUEST, data)
            
            if cookie != rules.MAGIC_COOKIE or msg_type != rules.MSG_TYPE_REQUEST:
                return  # Invalid packet
                
            player_name = rules.decode_string(name_bytes)
            print(f"Game started with team: {player_name}. Rounds: {rounds}")
            
            # Play Rounds
            for i in range(rounds):
                self.play_round(conn)
                
            print(f"Finished sending {rounds} rounds to {player_name}.")
            
        except Exception as e:
            print(f"Player handler error: {e}")
        finally:
            conn.close()

    def play_round(self, conn):
        deck = self.create_deck()
        player_cards = []
        dealer_cards = []
        
        # 1. Initial Deal 
        # Player gets 2 cards
        c1 = deck.pop(); player_cards.append(c1); self.send_card(conn, c1)
        c2 = deck.pop(); player_cards.append(c2); self.send_card(conn, c2)
        
        # Dealer gets 2 cards (1 sent, 1 hidden)
        d1 = deck.pop(); dealer_cards.append(d1); self.send_card(conn, d1)
        d2 = deck.pop(); dealer_cards.append(d2)  # Hidden

        # 2. Player Turn 
        player_busted = False
        while True:
            if self.calculate_sum(player_cards) > 21:
                player_busted = True
                break
                
            # Wait for decision
            try:
                data = conn.recv(rules.BUFFER_SIZE)
                cookie, mtype, action_bytes = struct.unpack(rules.STRUCT_PAYLOAD_PLAYER, data)
                action = action_bytes.decode('utf-8')
                
                if action == rules.ACTION_HIT:
                    new_card = deck.pop()
                    player_cards.append(new_card)
                    self.send_card(conn, new_card)
                else:  # Stand
                    break
            except:
                break

        # 3. Dealer Turn 
        dealer_sum = self.calculate_sum(dealer_cards)
        if not player_busted:
            self.send_card(conn, d2)  # Reveal hidden card
            
            while dealer_sum < 17:
                new_card = deck.pop()
                dealer_cards.append(new_card)
                dealer_sum = self.calculate_sum(dealer_cards)
                self.send_card(conn, new_card)

        # 4. Determine Winner 
        player_sum = self.calculate_sum(player_cards)
        result = rules.RESULT_TIE
        
        if player_sum > 21:
            result = rules.RESULT_LOSS
        elif dealer_sum > 21:
            result = rules.RESULT_WIN
        elif player_sum > dealer_sum:
            result = rules.RESULT_WIN
        elif dealer_sum > player_sum:
            result = rules.RESULT_LOSS
            
        # Send Result (Rank=0, Suit=0)
        self.send_packet(conn, result, 0, 0)

    def create_deck(self):
        # Rank 1-13, Suit 0-3 
        deck = [(r, s) for r in range(1, 14) for s in range(4)]
        random.shuffle(deck)
        return deck

    def calculate_sum(self, cards):
        total = 0
        aces = 0
        for rank, _ in cards:
            if rank == 1:  # Ace
                aces += 1
                total += 11
            elif rank >= 10: 
                total += 10
            else:
                total += rank
        
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def send_card(self, conn, card):
        # Sends a card with RESULT_PLAYING (0)
        self.send_packet(conn, rules.RESULT_PLAYING, card[0], card[1])

    def send_packet(self, conn, result, rank, suit):
        packet = struct.pack(
            rules.STRUCT_PAYLOAD_DEALER,
            rules.MAGIC_COOKIE,
            rules.MSG_TYPE_PAYLOAD,
            result,
            rank,
            suit
        )
        conn.sendall(packet)

if __name__ == "__main__":
    Dealer().start()
