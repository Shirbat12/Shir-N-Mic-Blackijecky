import socket
import struct
import RULES


class Player:
    def __init__(self):
        self.team_name = "LadyBugs"
        self.udp_port = RULES.UDP_PORT
        # A persistent buffer to store data across TCP stream reads (per connection)
        self.internal_buffer = b""

        # Timeouts
        self.udp_timeout = RULES.UDP_TIMEOUT
        self.tcp_connect_timeout = RULES.TCP_CONNECT_TIMEOUT
        self.tcp_recv_timeout = RULES.TCP_RECV_TIMEOUT

    def start(self):
        """
        Main client loop.
        The client run forever and after finishing a game it immediately return to listening for offers again.
        """
        print("Client started, listening for offer requests...")

        while True:
            # Get User Input (every new game)
            try:
                rounds_input = input("How many rounds to play? ")
                rounds = int(rounds_input)
            except ValueError:
                print("Invalid number.")
                continue  # do not exit, ask again

            # Reset buffer for a NEW TCP session (important!)
            self.internal_buffer = b""

            # UDP Discovery (Listen for Offer)
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Cross-platform compatibility for Port Reuse
            try:
                udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            udp_sock.bind(("", self.udp_port))
            udp_sock.settimeout(self.udp_timeout)

            dealer_ip, dealer_port = None, None

            print(f"Listening on port {self.udp_port}...")

            while True:
                try:
                    data, addr = udp_sock.recvfrom(RULES.BUFFER_SIZE)
                except socket.timeout:
                    print("Still waiting for offers...")
                    continue

                try:
                    cookie, mtype, port, name_bytes = struct.unpack(RULES.STRUCT_OFFER, data)
                    if cookie == RULES.MAGIC_COOKIE and mtype == RULES.MSG_TYPE_OFFER:
                        dealer_name = RULES.decode_string(name_bytes)
                        dealer_ip = addr[0]
                        dealer_port = port
                        print(f"Received offer from {dealer_name} at {dealer_ip}")
                        break
                except struct.error:
                    # Ignore invalid/partial UDP packets
                    continue

            udp_sock.close()

            # TCP Connection + Play
            if dealer_ip and dealer_port:
                self.connect_and_play(dealer_ip, dealer_port, rounds)

            # After finishing the game, the while True loop continues,
            # and we go back to asking for rounds + listening for offers again.

    def connect_and_play(self, ip, port, rounds):
        """
        Connect to the dealer over TCP, send a request, and play the requested rounds.
        """
        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.settimeout(self.tcp_connect_timeout)
            tcp_sock.connect((ip, port))

            # After connect we use a receive timeout
            tcp_sock.settimeout(self.tcp_recv_timeout)

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
                print(f"\nRound {i + 1}")
                res = self.play_round(tcp_sock)

                if res == RULES.RESULT_WIN:
                    print("Result: You Won!")
                    wins += 1
                elif res == RULES.RESULT_LOSS:
                    print("Result: You Lost.")
                else:
                    print("Result: Tie.")

            # Avoid division by zero if rounds is 0
            win_rate = (wins / rounds) if rounds > 0 else 0
            print(f"\nGame Over. Win rate: {win_rate:.2f}")

            tcp_sock.close()

        except Exception as e:
            print(f"Connection error: {e}")

    def play_round(self, sock):
        """
        Plays a single round.
        - reads dealer packets using an internal buffer
        - prints cards and hand total before asking for h/s
        - sends "Hittt" / "Stand" decisions using the protocol format
        """
        my_cards = []
        dealer_cards = []
        my_turn = True

        msg_size = struct.calcsize(RULES.STRUCT_PAYLOAD_DEALER)

        while True:
            # Ensure we have at least one full packet in the buffer
            while len(self.internal_buffer) < msg_size:
                try:
                    data = sock.recv(RULES.BUFFER_SIZE)
                except socket.timeout:
                    # If dealer is slow / network is noisy, we keep waiting
                    continue

                if not data:
                    return RULES.RESULT_TIE  # Error or disconnect

                self.internal_buffer += data

            # Pop exactly one packet from the front
            packet = self.internal_buffer[:msg_size]
            self.internal_buffer = self.internal_buffer[msg_size:]

            # Process the packet
            try:
                cookie, mtype, result, rank, suit = struct.unpack(RULES.STRUCT_PAYLOAD_DEALER, packet)
                if cookie != RULES.MAGIC_COOKIE:
                    continue

                # If result is not Playing (0), the round is over
                if result != RULES.RESULT_PLAYING:
                    return result

                # Parse card
                card_str, card_val = RULES.parse_card(rank, suit)

                # Logic to deduce whose card it is
                is_my_card = False
                if len(my_cards) < 2:
                    is_my_card = True
                elif len(dealer_cards) < 1:
                    is_my_card = False
                elif my_turn:
                    is_my_card = True
                else:
                    is_my_card = False

                if is_my_card:
                    my_cards.append(card_val)
                    print(f"Player received: {card_str}")
                else:
                    dealer_cards.append(card_val)
                    print(f"Dealer received: {card_str}")

                # Game Decision Logic
                if my_turn and len(my_cards) >= 2 and len(dealer_cards) >= 1:
                    my_sum = self.calculate_sum(my_cards)

                    if my_sum > 21:
                        print(f"Bust! Total: {my_sum}")
                        my_turn = False
                        # Wait for server to send the final Loss packet
                    elif is_my_card or (len(my_cards) == 2 and len(dealer_cards) == 1):
                        print(f"Your Hand Total: {my_sum}")

                        # Validate user input: only h/s allowed
                        move = ""
                        while move not in ("h", "s"):
                            move = input("Action (h/s): ").strip().lower()

                        action_str = RULES.ACTION_HIT if move == "h" else RULES.ACTION_STAND
                        if move == "s":
                            my_turn = False

                        # Send Decision
                        decision_packet = struct.pack(
                            RULES.STRUCT_PAYLOAD_PLAYER,
                            RULES.MAGIC_COOKIE,
                            RULES.MSG_TYPE_PAYLOAD,
                            action_str.encode('utf-8')
                        )
                        sock.sendall(decision_packet)

            except struct.error as e:
                print(f"Struct error: {e}")
                continue

    def calculate_sum(self, cards):
        """
        Helper for Client UI.
        Aces are stored as 11, then reduced to 1 if we bust.
        """
        total = sum(cards)
        aces = cards.count(11)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total


if __name__ == "__main__":
    Player().start()
