# Blackijecky - Intro to Computer Networks Hackathon
**Team Name:** Lady Bugs

## The Project
This project is a multiplayer Blackjack game implementation.
The system consists of a **Server** (Dealer) that manages the game and **Clients** (Players) that connect to play.

## Project Structure
We organized the code into 3 separate files to ensure separation of concerns and code reusability:

1.  **`RULES.py` (Constants file):**
    * Holds all shared definitions: Magic Cookie, Port numbers, and Message Types.
    * Contains the `struct` formats to ensure the Server and Client speak the same language.

2.  **`dealer.py` (Server):**
    * Manages the card deck and game logic.
    * Handles multiple players simultaneously using threading.

3.  **`player.py` (Client):**
    * Handles user input ("Hit" or "Stand").
    * Displays game updates received from the server.

## Network Protocols
The application uses two network protocols for different stages of the game:

* **UDP (User Datagram Protocol):** Used for **Game Discovery**.
    * The Server broadcasts "Offer" messages to the local network so Clients can find it without knowing its IP address in advance.
* **TCP (Transmission Control Protocol):** Used for the **Active Game**.
    * Once a Client receives an offer, it establishes a reliable TCP connection with the Server to exchange cards, moves, and results.


## How to Run

### Prerequisites

* Ensure you have **Python 3.x** installed.


* Make sure all 3 files (`dealer.py`, `player.py`, `RULES.py`) are in the same folder.

### Step 1: Start the Server (Dealer)

The server must be running first to broadcast offers to potential players.

1. Open a terminal window (Terminal A).
2. Navigate to the project folder.
3. Run the server:
```bash
python dealer.py

```


4. **Expected Output:** You should see a message indicating the server has started, found its IP, and is broadcasting "Offer" messages via UDP.
> *Dealer started, listening on IP address 192.168.1.X*



### Step 2: Start a Client (Player)

1. Open a **new, separate** terminal window (Terminal B).
2. Navigate to the project folder.
3. Run the client:
```bash
python player.py

```


4. **Interaction:**
* The client will listen for the server's UDP broadcast.
* Once found, it will prompt you: `How many rounds to play?`.
* Enter a number (e.g., `3`) and press Enter.



### Step 3: Playing the Game

1. The game loop begins automatically over TCP.
2. **Your Turn:**
* You will see your cards and your total sum.
* When prompted `Action (h/s):`, type:
* `h` to **Hit** (get another card).
* `s` to **Stand** (end your turn).




3. **Dealer's Turn:** The dealer will reveal their cards and play according to the logic (Hit until 17).
4. **Result:** The round result (Win/Loss/Tie) will be displayed.
5. This repeats for the number of rounds you requested.

### Step 4: Multiplayer Simulation (Optional)

To test the threading capabilities of the server:

1. Keep the **Server** (Terminal A) running.
2. Open multiple new terminal windows (Terminal C, Terminal D...).
3. Run `python player.py` in each of them.
4. The server will handle all games simultaneously!
