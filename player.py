import socket
import struct
import RULES 

class Player:
    def __init__(self):
        self.team_name = "PythonPlayer"
        self.udp_port = RULES.UDP_PORT
        # NEW: A persistent buffer to store data across rounds
        self.internal_buffer = b""

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
        
        # Cross-platform compatibility for Port Reuse
        try:
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            # Fallback for Windows which doesn't support SO_REUSEPORT
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        udp_sock.bind(("", self.udp_port))

        dealer_ip, dealer_port = None, None

        while True:
            data, addr = udp_sock.recvfrom(RULES.BUFFER_SIZE)
            try:
                cookie, mtype, port, name_bytes = struct.unpack(RULES.STRUCT_OFFER, data)
                if cookie == RULES.MAGIC_COOKIE and mtype == RULES.MSG_TYPE_OFFER:
                    dealer_name = RULES.decode_string(name_bytes)
                    dealer_ip = addr[0]
                    dealer_port = port
                    print(f"Received offer from {dealer_name} at {dealer_ip}")
                    break
            except struct.error:
                continue 
        
        udp_sock.close()

        # 3. TCP Connection
        self.connect_and_play(dealer_ip, dealer_port, rounds)

    def connect_and_play(self, ip, port, rounds):
        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.connect((ip, port))
            
            # Send Request
            packet = struct.pack(
                RULES.STRUCT_REQUEST,
                RULES.MAGIC_COOKIE,
                RULES.MSG_TYPE_REQUEST,
                rounds,
                RULES.format_string(self.team_name)
            )
            tcp_sock.sendall(packet)

            wins = 0
            for i in range(rounds):
                print(f"\n--- Round {i+1}")
                res = self.play_round(tcp_sock)
                
                if res == RULES.RESULT_WIN:
                    print("Result: You Won!")
                    wins += 1
                elif res == RULES.RESULT_LOSS:
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
        
        # Packet size is exactly 9 bytes (Header + Payload)
        msg_size = struct.calcsize(RULES.STRUCT_PAYLOAD_DEALER)
        
        while True:
            # STEP 1: Ensure we have at least one full packet in the buffer
            while len(self.internal_buffer) < msg_size:
                data = sock.recv(RULES.BUFFER_SIZE)
                if not data: return RULES.RESULT_TIE # Error or disconnect
                self.internal_buffer += data
            
            # STEP 2: Pop exactly one packet from the front
            packet = self.internal_buffer[:msg_size]
            self.internal_buffer = self.internal_buffer[msg_size:] # Save the rest for later!

            # STEP 3: Process the packet
            try:
                cookie, mtype, result, rank, suit = struct.unpack(RULES.STRUCT_PAYLOAD_DEALER, packet)
                if cookie != RULES.MAGIC_COOKIE: continue

                # If result is not Playing (0), the round is over
                if result != RULES.RESULT_PLAYING:
                    return result

                # Parse card
                card_str, card_val = RULES.parse_card(rank, suit)
                
                # Logic to deduce whose card it is
                    is_my_card = False
                if len(my_cards) < 2:          is_my_card = True
                elif len(dealer_cards) < 1:    is_my_card = False
                elif my_turn:                  is_my_card = True
                else:                          is_my_card = False
                
                if is_my_card:
                    my_cards.append(card_val)
                    print(f"Player received: {card_str}")
                else:
                    dealer_cards.append(card_val)
                    print(f"Dealer received: {card_str}")

            except struct.error:
                continue
            
            # STEP 4: Game Decision Logic
                if my_turn and len(my_cards) >= 2 and len(dealer_cards) >= 1:
                    my_sum = self.calculate_sum(my_cards)
                    
                    if my_sum > 21:
                        print(f"Bust! Total: {my_sum}")
                        my_turn = False 
                        # Server will send Loss packet next
                    else:
                        print(f"Your Hand Total: {my_sum}")
                        move = input("Action (h/s): ").lower()
                        
                    action_str = RULES.ACTION_STAND
                        if move == 'h':
                        action_str = RULES.ACTION_HIT
                        else:
                            my_turn = False
                            
                        # Send Decision
                        decision_packet = struct.pack(
                        RULES.STRUCT_PAYLOAD_PLAYER,
                        RULES.MAGIC_COOKIE,
                        RULES.MSG_TYPE_PAYLOAD,
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

