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
        
        # 1. Setup UDP Socket (For Broadcasting Offers)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enable broadcasting mode to send to everyone on the network
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # 2. Setup TCP Socket (For Game Connections)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind to port 0: Let the OS choose an available port
        self.tcp_socket.bind(('', 0)) 
        # Get the actual port number assigned by the OS
        self.tcp_port = self.tcp_socket.getsockname()[1]
        self.tcp_socket.listen(5)
        
        print(f"Dealer started, listening on IP address {self.server_ip}") 

    def get_local_ip(self):
        """
        Helper method to find the machine's actual IP address 
        by connecting to an external server (Google DNS).
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        """Main server loop."""
        # Start the UDP broadcast in a separate thread so it runs in the background.
        # Daemon thread closes automatically when the main program exits.
        threading.Thread(target=self.broadcast_offers, daemon=True).start()
        
        # Main loop: Accept new TCP connections from players
        while self.running:
            try:
                # accept() blocks until a new client connects.
                # It returns a NEW socket specifically for this player.
                player_socket, player_address = self.tcp_socket.accept()
                print(f"New connection from {player_address}")
                
                # Handle each player in a new, separate thread.
                # This allows multiple players to play at the same time (Concurrency).
                threading.Thread(target=self.handle_player, args=(player_socket,)).start()
            except Exception as e:
                print(f"Accept error: {e}")

    def broadcast_offers(self):
        """Sends UDP Offer packets every 1 second to the network."""
        # Create the Offer packet using the struct format from RULES.py
        packet = struct.pack(
            RULES.STRUCT_OFFER,
            RULES.MAGIC_COOKIE,             # Protocol security check
            RULES.MSG_TYPE_OFFER,           # Message Type: Offer
            self.tcp_port,                  # Send our TCP port so clients know where to connect
            RULES.format_string(self.team_name)
        )
        
        while self.running:
            try:
                # Send to the broadcast address (255.255.255.255)
                self.udp_socket.sendto(packet, (RULES.BROADCAST_IP, RULES.UDP_PORT))
                time.sleep(1) 
            except Exception as e:
                print(f"Broadcast failed: {e}")

    def handle_player(self, player_socket):
        """Manages the full game session for a single connected player."""
        try:
            # 1. Receive the initial Request packet
            # The code waits here (blocks) until data arrives. No busy waiting.
            data = player_socket.recv(RULES.BUFFER_SIZE)
            if not data: return
            
            # Unpack the binary data
            cookie, msg_type, rounds, name_bytes = struct.unpack(RULES.STRUCT_REQUEST, data)
            
            # Validate protocol (Magic Cookie must match)
            if cookie != RULES.MAGIC_COOKIE or msg_type != RULES.MSG_TYPE_REQUEST:
                print("Invalid packet received.")
                return 
                
            player_name = RULES.decode_string(name_bytes)
            print(f"Game started with team: {player_name}. Rounds: {rounds}")
            
            # 2. Play the requested number of rounds
            for i in range(rounds):
                self.play_round(player_socket)
                
            print(f"Finished sending {rounds} rounds to {player_name}.")
            
        except Exception as e:
            print(f"Player handler error: {e}")
        finally:
            # Always close the connection when done to free resources
            player_socket.close()

    def play_round(self, player_socket):
        """Logic for a single round of Blackjack."""
        deck = self.create_deck()
        player_cards = []
        dealer_cards = []
        
        # Step 1: Initial Deal
        # Player gets 2 cards (sent immediately via TCP)
        c1 = deck.pop(); player_cards.append(c1); self.send_card(player_socket, c1)
        c2 = deck.pop(); player_cards.append(c2); self.send_card(player_socket, c2)
        
        # Dealer gets 2 cards (1 visible sent to player, 1 hidden)
        d1 = deck.pop(); dealer_cards.append(d1); self.send_card(player_socket, d1)
        d2 = deck.pop(); dealer_cards.append(d2)  # Kept in memory, not sent yet

        # Step 2: Player Turn
        player_busted = False
        while True:
            # Calculate player's hand
            if self.calculate_sum(player_cards) > 21:
                player_busted = True
                break # Player lost (Bust)
                
            # Wait for player decision (Hit or Stand)
            try:
                # recv() blocks execution until the player sends a decision
                data = player_socket.recv(RULES.BUFFER_SIZE)
                cookie, mtype, action_bytes = struct.unpack(RULES.STRUCT_PAYLOAD_PLAYER, data)
                action = action_bytes.decode('utf-8')
                
                if action == RULES.ACTION_HIT:
                    new_card = deck.pop()
                    player_cards.append(new_card)
                    self.send_card(player_socket, new_card) # Send new card to player
                else:  # Stand
                    break
            except:
                break

        # Step 3: Dealer Turn
        dealer_sum = self.calculate_sum(dealer_cards)
        
        # Only play dealer turn if player did not bust
        if not player_busted:
            self.send_card(player_socket, d2)  # Reveal hidden card now
            
            # Dealer logic: must draw until 17 or higher
            while dealer_sum < 17:
                new_card = deck.pop()
                dealer_cards.append(new_card)
                dealer_sum = self.calculate_sum(dealer_cards)
                self.send_card(player_socket, new_card)

        # Step 4: Determine Winner
        player_sum = self.calculate_sum(player_cards)
        result = RULES.RESULT_TIE
        
        if player_sum > 21:
            result = RULES.RESULT_LOSS
        elif dealer_sum > 21:
            result = RULES.RESULT_WIN
        elif player_sum > dealer_sum:
            result = RULES.RESULT_WIN
        elif dealer_sum > player_sum:
            result = RULES.RESULT_LOSS
            
        # Send the final result packet (End of round)
        self.send_packet(player_socket, result, 0, 0)

    def create_deck(self):
        """Creates and shuffles a standard 52-card deck."""
        # Rank 1-13, Suit 0-3 
        deck = [(r, s) for r in range(1, 14) for s in range(4)]
        random.shuffle(deck)
        return deck

    def calculate_sum(self, cards):
        """Calculates hand value, handling Aces (1 or 11)."""
        total = 0
        aces = 0
        for rank, _ in cards:
            if rank == 1:  # Ace
                aces += 1
                total += 11
            elif rank >= 10: # Face cards (J, Q, K)
                total += 10
            else:
                total += rank
        
        # Adjust Aces if total > 21
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def send_card(self, player_socket, card):
        """Helper to send a card packet (Result=Playing)."""
        self.send_packet(player_socket, RULES.RESULT_PLAYING, card[0], card[1])

    def send_packet(self, player_socket, result, rank, suit):
        """Helper to pack and send a TCP packet using the protocol struct."""
        packet = struct.pack(
            RULES.STRUCT_PAYLOAD_DEALER,
            RULES.MAGIC_COOKIE,
            RULES.MSG_TYPE_PAYLOAD,
            result,
            rank,
            suit
        )
        player_socket.sendall(packet)

if __name__ == "__main__":
    Dealer().start()