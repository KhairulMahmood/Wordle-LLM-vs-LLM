# LLM Wordle Project Documentation

## 1. Project Overview

This document outlines the design and implementation of an evolved hobby project that pits two large language models (LLMs) against each other in the popular word game Wordle. Based on insights from a previous iteration, the role of the Game Master (GM) will now be handled by a deterministic Python script, allowing the LLMs to focus on their strengths as creative players. The project aims to demonstrate inter-LLM competition, robust game orchestration, and the creation of a full-stack application with a web-based user interface.

## 2. System Architecture (Revised)

The LLM Wordle project is designed with a microservices-oriented architecture, separating concerns into distinct server processes that communicate via well-defined APIs. This revised approach enhances modularity, scalability, and maintainability, allowing for independent development and deployment of each component. The system now comprises two Player LLM server components, and a central Referee Server that also acts as the Scripted Game Master, along with a web-based frontend.

### 2.1. Component Breakdown (Revised)

#### 2.1.1. Player 1 Server

*   **Role:** Acts as the first Wordle player, generating word guesses based on game history and feedback.
*   **Technology:** Python Flask application.
*   **LLM Integration:** Wraps a `llama.cpp` instance, running within a Windows Subsystem for Linux (WSL) Ubuntu environment. This allows leveraging the performance benefits of `llama.cpp` on Linux.
*   **Communication Protocol:** Exposes a RESTful API endpoint (e.g., `http://localhost:5001/get_guess`) that accepts game state data (including past guesses and feedback) in JSON format. It returns a JSON object containing the LLM's five-letter word guess and optional conversational comments.
*   **Location:** Runs within the WSL Ubuntu environment, accessible from the Windows host via `localhost` forwarding.

#### 2.1.2. Player 2 Server

*   **Role:** Acts as the second Wordle player, competing against Player 1 by generating word guesses based on game history and feedback.
*   **Technology:** Python Flask application.
*   **LLM Integration:** Wraps an Ollama instance, running directly on the Windows host. Ollama provides a convenient way to run various LLMs locally.
*   **Communication Protocol:** Exposes a RESTful API endpoint (e.g., `http://localhost:5002/get_guess`) that accepts game state data in JSON format. It returns a JSON object containing the LLM's five-letter word guess and optional conversational comments.
*   **Location:** Runs directly on the Windows host.

#### 2.1.3. Referee Server (with Scripted Game Master)

*   **Role:** The central orchestrator of the game, managing the overall game flow, maintaining the authoritative game state, acting as the deterministic Game Master, and serving the web-based user interface.
*   **Technology:** Python Flask application with Flask-SocketIO for real-time communication.
*   **Scripted Game Master Logic:** This server now contains the logic to:
    *   Choose a secret Wordle word.
    *   Evaluate player guesses against the secret word and generate the `GXYYX` feedback deterministically (without an LLM).
    *   Validate player guesses (e.g., 5 letters, valid word).
*   **Communication Protocol (to Player LLM Servers):** Acts as a client, making HTTP POST requests to both Player 1 and Player 2 servers to retrieve their guesses. All data exchanged with LLM servers is in JSON format.
*   **Communication Protocol (to Frontend):** Acts as a server, serving the static HTML, CSS, and JavaScript files for the web interface. It also establishes a persistent, bi-directional communication channel with the frontend via WebSockets (Socket.IO) to push real-time game updates.
*   **Location:** Runs directly on the Windows host.

#### 2.1.4. Web Frontend

*   **Role:** Provides the interactive graphical user interface for the user to observe the game progression, including the Wordle grid, LLM commentary, and game status.
*   **Technology:** HTML, CSS, and JavaScript.
*   **Communication Protocol:** Connects to the Referee Server via WebSockets (Socket.IO) to receive real-time game state updates. It also sends control signals (e.g., a 'Start Game' button click) back to the Referee Server.
*   **Location:** Runs in the user's web browser.

### 2.2. Communication Flow (Revised)

The communication within the system follows a clear client-server pattern, with the Referee Server acting as the central hub and now also performing the Game Master duties. All data transfer between components leverages JSON for structured and reliable communication.

1.  **User Interaction (Frontend to Referee):** The user initiates actions (e.g., 'Start Game') via the web frontend. This triggers a WebSocket event sent from the frontend (JavaScript) to the Referee Server (Flask-SocketIO).
2.  **Game Orchestration (Referee to Player LLM Servers):** Upon receiving a command or during its game loop, the Referee Server makes HTTP POST requests to both Player 1 and Player 2 servers. These requests contain the necessary game state information in JSON format.
3.  **LLM Processing (Player LLM Servers):** Player 1 and Player 2 servers process the incoming JSON data, interact with their respective LLMs (llama.cpp or Ollama), and generate their responses. They then return a JSON object containing their word guess and conversational comments.
4.  **Scripted Game Master Evaluation (Referee):** The Referee Server receives the JSON responses from both Player LLMs. It then *internally* evaluates each player's guess against the secret word to generate the emoji-based feedback (e.g., `🟩🟨⬜⬜⬜`). This feedback is no longer generated by an LLM.
5.  **State Update and Real-time Display (Referee to Frontend):** The Referee Server updates its internal game state with both players' guesses and the deterministically generated feedback. It then broadcasts the new state (or relevant parts of it) to the connected web frontend via WebSocket events. The frontend's JavaScript then dynamically updates the UI to show both players' progress.

### 2.3. Data Structures (JSON Schemas) (Revised)

To ensure robust and predictable communication, all data exchanged between the Referee Server and the Player LLM servers adheres to predefined JSON schemas. The Game Master logic is now internal to the Referee Server, simplifying the external data flow.

#### 2.3.1. Referee to Player Server Request

This JSON object is sent by the Referee Server to a Player Server (Player 1 or Player 2) to request a new guess. It provides the Player LLM with all necessary context from the ongoing game.

```json
{
  "turn_number": <integer>,          // Current turn number
  "max_turns": <integer>,            // Maximum allowed turns for the game
  "history": [
    { 
      "guess": "<string>",         // Previous guess (5-letter word)
      "feedback": "<string>"       // Feedback for the previous guess (e.g., "🟩🟨⬜⬜⬜")
    }
  ], 
  "player_message": "<string>"     // Optional: Natural language message from the Referee to the Player LLM
}
```

#### 2.3.2. Player Server to Referee Response

This JSON object is returned by a Player Server to the Referee Server, containing the Player LLM's chosen word and any accompanying commentary.

```json
{
  "word_guess": "<string>",        // The 5-letter word guessed by the Player LLM
  "comments": "<string>"         // Optional: Conversational comments or reasoning from the Player LLM
}
```

### 2.4. Game State Management (Revised)

The Referee Server maintains the authoritative game state, which now includes:

*   The secret 5-letter Wordle word.
*   The current turn number.
*   The maximum allowed turns.
*   A historical log of all guesses made by *both* players and their corresponding feedback received.
*   Flags for game status (e.g., `game_over`, `win_player1`, `win_player2`, `draw`).

This state is updated after each interaction with the LLM servers and is used to drive the game logic and update the frontend. The state is reset for each new game initiated by the user.



### 2.5. Scripted Game Master Logic

With the revised architecture, the Referee Server now incorporates the full logic of the Wordle Game Master. This change ensures deterministic and reliable feedback generation, removing the inconsistencies sometimes observed with LLM-based feedback. The Referee Server is responsible for:

*   **Secret Word Selection:** Randomly choosing a valid 5-letter Wordle word from a predefined dictionary at the start of each game.
*   **Guess Validation:** Checking if a player's submitted guess is a valid 5-letter word and present in the dictionary (optional, but good practice for a robust game).
*   **Feedback Generation:** Applying the standard Wordle rules to compare a player's guess against the secret word and generating the precise emoji-based feedback string (e.g., `🟩🟨⬜⬜⬜`). This process is purely algorithmic and does not involve an LLM.

This consolidation of the Game Master role within the Referee Server simplifies the overall system, reduces external dependencies for core game mechanics, and allows the Player LLMs to focus solely on their strategic guessing capabilities.
