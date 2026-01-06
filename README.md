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

## How to Run code

### 1. Start the Server
Open a terminal and run:
```bash
python dealer.py
