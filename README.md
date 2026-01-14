# Blackijecky – Intro to Computer Networks Hackathon

**Team Name:** Lady Bugs

---

## The Project

This project is a multiplayer Blackjack game implementation.

The system consists of a **Server** (Dealer) that manages the game logic and **Clients** (Players) that connect to play the game over the network.

---

## Project Structure

We organized the code into 3 separate files:

1. **`RULES.py` (Constants file)**

   * Holds all shared protocol definitions: Magic Cookie, port numbers, and message types.
   * Contains all `struct` formats so the Server and Client speak the same binary language.
   * Defines common constants such as timeouts and dealer rules.

2. **`dealer.py` (Server)**

   * Manages the card deck and the Blackjack game logic.
   * Broadcasts offers using UDP.
   * Handles multiple players simultaneously using threads.

3. **`player.py` (Client)**

   * Handles user input ("Hit" or "Stand").
   * Displays all game updates received from the server.
   * Runs continuously and reconnects automatically after each game.

---

## Network Protocols

The application uses two different protocols, each for a different stage:

* **UDP – Game Discovery**
  The Server broadcasts "Offer" messages every second so Clients can find it without knowing the IP address in advance.

* **TCP – Active Game Session**
  After receiving an offer, the Client connects to the Server using TCP to exchange cards, moves, and round results reliably.

---

## How to Run

### Prerequisites

* Python **3.x** installed.
* All 3 files (`dealer.py`, `player.py`, `RULES.py`) must be in the same folder.

---

### Step 1: Start the Server (Dealer)

1. Open a terminal window.
2. Navigate to the project folder.
3. Run:

```bash
python dealer.py
```

**Expected Output:**

```
Dealer started, listening on IP address 192.168.1.X
```

The server will now broadcast UDP offers every second.

---

### Step 2: Start a Client (Player)

1. Open a **new** terminal window.
2. Navigate to the same project folder.
3. Run:

```bash
python player.py
```

The client will listen for offers and then ask:

```
How many rounds to play?
```

Enter a number (for example: `3`) and press Enter.

---

### Step 3: Playing the Game

* You will see your cards and your hand total.
* When prompted:

```
Action (h/s):
```

Type:

* `h` – Hit (get another card)
* `s` – Stand (end your turn)

The dealer will then reveal their cards, play according to the rules (Hit until 17),
and the round result will be printed.

This repeats for the number of rounds you requested.

---

### Step 4: Multiplayer Simulation (Optional)

1. Keep the Server running.
2. Open multiple new terminal windows.
3. Run `python player.py` in each window.

The server will handle all players at the same time using threads.

---

## Error Handling & Timeouts

Real networks are not perfect, so we added basic error handling to make the game stable.

### Client (`player.py`)

* **Runs continuously:**
  After a game ends, the client immediately returns to listening for new offers.

* **UDP timeout:**
  If no offer is received for a few seconds, the client prints
  `Still waiting for offers...` and keeps listening.

* **TCP timeouts:**
  Timeouts are set for connecting and receiving data, so the client will not block forever.

* **Safe user input:**
  Only `h` or `s` are accepted when choosing an action.

* **TCP stream-safe receiving:**
  The client uses an internal buffer to make sure full packets are received before unpacking.

### Server (`dealer.py`)

* **Thread-per-client design:**
  Each player is handled in a separate thread.

* **TCP stream-safe receiving (`recvall`):**
  The server reads exactly the needed number of bytes for each packet before unpacking.

* **Protocol validation:**
  The Magic Cookie and Message Type are checked for every packet.

* **Graceful disconnect handling:**
  If a client disconnects unexpectedly, the server ends the session safely.

---

## Known Limitations

* The project assumes a local network (LAN) environment for UDP discovery.
* If a player disconnects mid-round, the server safely terminates that session.

---

Good luck and enjoy the game! 🃏
