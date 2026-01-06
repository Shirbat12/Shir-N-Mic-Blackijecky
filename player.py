import socket
import struct
import RULES 

class Player:
    def __init__(self):
        self.team_name = "PythonPlayer"
        self.udp_port = rules.UDP_PORT

    def start(self):
        print("Client started, listening for offer requests...")
        
        # 1. Get User Input
        try:
            rounds = int(input("How many rounds to play? "))
        except ValueError:
            print("Invalid number.")
            return

        # 2. UDP Discovery (Listen for Offer)
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # FIX: Cross-platform compatibility for Port Reuse
        try:
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            # Fallback for Windows which doesn't support SO_REUSEPORT
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        udp_sock.bind(("", self.udp_port))

        dealer_ip, dealer_port = None, None

        while True:
            data, addr = udp_sock.recvfrom(rules.BUFFER_SIZE)
            try:
                cookie, mtype, port, name_bytes = struct.unpack(rules.STRUCT_OFFER, data)
                if cookie == rules.MAGIC_COOKIE and mtype == rules.MSG_TYPE_OFFER:
                    dealer_name = rules.decode_string(name_bytes)
                    dealer_ip = addr[0]
                    dealer_port = port
                    print(f"Received offer from {dealer_name} at {dealer_ip}")
                    break
            except struct.error:
                continue # Ignore bad packets
        
        udp_sock.close()

        # 3. TCP Connection
        self.connect_and_play(dealer_ip, dealer_port, rounds)

    def connect_and_play(self, ip, port, rounds):
        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.connect((ip, port))
            
            # Send Request
            packet = struct.pack(
                rules.STRUCT_REQUEST,
                rules.MAGIC_COOKIE,
                rules.MSG_TYPE_REQUEST,
                rounds,
                rules.format_string(self.team_name)
            )
            tcp_sock.sendall(packet)

            wins = 0
            for i in range(rounds):
                print(f"\n--- Round {i+1} ---")
                res = self.play_round(tcp_sock)
                
                if res == rules.RESULT_WIN:
                    print("Result: You Won!")
                    wins += 1
                elif res == rules.RESULT_LOSS:
                    print("Result: You Lost.")
                else:
                    print("Result: Tie.")
            
            print(f"\nGame Over. Win rate: {wins/rounds:.2f}")
            tcp_sock.close()
            
        except Exception as e:
            print(f"Connection error: {e}")

    def play_round(self, sock):
        my_cards = []
        dealer_cards = [] 
        my_turn = True 
        
        while True:
            data = sock.recv(rules.BUFFER_SIZE)
            if not data: break
            
            try:
                # Unpack Dealer Packet
                cookie, mtype, result, rank, suit = struct.unpack(rules.STRUCT_PAYLOAD_DEALER, data)
                if cookie != rules.MAGIC_COOKIE: continue

                # If result is not Playing(0), round is over
                if result != rules.RESULT_PLAYING:
                    return result

                # Parse card
                card_str, card_val = rules.parse_card(rank, suit)
                
                # Logic to deduce whose card it is based on game flow:
                is_my_card = False
                
                # First 2 cards -> Player
                if len(my_cards) < 2:
                    is_my_card = True
                # 3rd card -> Dealer (Visible)
                elif len(dealer_cards) < 1:
                    is_my_card = False 
                # While my_turn -> Player
                elif my_turn:
                    is_my_card = True
                # After Stand -> Dealer
                else:
                    is_my_card = False
                
                if is_my_card:
                    my_cards.append(card_val)
                    print(f"Player received: {card_str}")
                else:
                    dealer_cards.append(card_val)
                    print(f"Dealer received: {card_str}")

                # Decision Logic
                # We decide only if it's our turn, we have 2+ cards, and dealer has 1 visible
                if my_turn and len(my_cards) >= 2 and len(dealer_cards) >= 1:
                    my_sum = self.calculate_sum(my_cards)
                    
                    if my_sum > 21:
                        print(f"Bust! Total: {my_sum}")
                        my_turn = False 
                        # Server will send Loss packet next
                    else:
                        print(f"Your Hand Total: {my_sum}")
                        move = input("Action (h/s): ").lower()
                        
                        action_str = rules.ACTION_STAND
                        if move == 'h':
                            action_str = rules.ACTION_HIT
                        else:
                            my_turn = False
                            
                        # Send Decision
                        decision_packet = struct.pack(
                            rules.STRUCT_PAYLOAD_PLAYER,
                            rules.MAGIC_COOKIE,
                            rules.MSG_TYPE_PAYLOAD,
                            action_str.encode('utf-8')
                        )
                        sock.sendall(decision_packet)

            except struct.error:
                continue

    def calculate_sum(self, cards):
        # Helper for Client UI (matches server logic)
        total = sum(cards)
        aces = cards.count(11)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

if __name__ == "__main__":
    Player().start()

