#!/usr/bin/env python3
"""
LLM Wordle Player 1 Server
Runs in WSL Ubuntu environment and integrates with llama.cpp
Provides word guessing functionality for the Wordle game
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import subprocess
import random
import logging
import os
import re
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class WordlePlayer:
    """
    Handles the Wordle player logic and llama.cpp integration
    """
    
    def __init__(self, player_name="Player 1"):
        self.player_name = player_name
        self.llama_cpp_path = "/path/to/llama.cpp/build/bin/llama-run"  # Update this path
        self.model_path = "/path/to/your/model.gguf"     # Update this path
        
        # Common 5-letter words for fallback
        self.common_words = [
            "AUDIO", "CRANE", "SLATE", "ROAST", "PLANT", "BEAST", "HEART",
            "SMART", "LIGHT", "NIGHT", "SIGHT", "FIGHT", "RIGHT", "MIGHT",
            "ABOUT", "HOUSE", "MOUSE", "HORSE", "NURSE", "PURSE", "CURSE",
            "BREAD", "DREAM", "STEAM", "CREAM", "CLEAN", "CLEAR", "LEARN"
        ]
        
    def construct_prompt(self, game_data: Dict[str, Any]) -> str:
        """
        Constructs a detailed prompt for the llama.cpp model
        """
        turn_number = game_data.get('turn_number', 1)
        max_turns = game_data.get('max_turns', 6)
        history = game_data.get('history', [])
        player_message = game_data.get('player_message', '')
        
        prompt = f"""You are {self.player_name}, a contestant in a high-stakes Wordle game show. Be conversational, explain your thought process, and feel free to show some personality! You are competing against another AI.

Game Rules:
- You have {max_turns} attempts to guess the correct word
- This is attempt {turn_number} of {max_turns}
- After each guess, you receive feedback:
  - 🟩: Letter is correct and in the right position
  - 🟨: Letter is in the word but in the wrong position  
  - ⬜: Letter is not in the word at all

"""
        
        if history:
            prompt += f"Your previous guesses and feedback:\n"
            for i, entry in enumerate(history, 1):
                guess = entry.get('guess', '')
                feedback = entry.get('feedback', '')
                prompt += f"Guess {i}: {guess} -> Feedback: {feedback}\n"
            prompt += "\n"
        elif turn_number == 1:
            prompt += "This is your first turn. Make a strong opening guess to gather information about vowels and common consonants.\n\n"
        
        if player_message:
            prompt += f"Game Message: {player_message}\n\n"
        
        prompt += f"""Now, as {self.player_name}, it's your time to shine! Analyze the board, explain your brilliant strategy, and then make your guess.

**CRITICAL RULE: Your guess MUST be a single, valid, 5-letter English word.**

Provide your reasoning, then on a separate line, submit your guess using the exact format `GUESS: YOURWORD`.
This is the only way your guess will be registered.

Example:
Okay, the board is wide open. I need a word with common vowels to get the most information. I'm feeling confident about this one!
GUESS: AUDIO"""
        
        return prompt
    
    def call_llama_cpp(self, prompt: str) -> str:
        """
        Calls llama.cpp with the given prompt and returns the response
        """
        try:
            # Construct the llama.cpp command
            cmd = [
                self.llama_cpp_path,
                "-m", self.model_path,
                "-p", prompt,
                "-n", "200",  # Max tokens
                "--temp", "0.8",
                "--top-p", "0.9",
                "-c", "2048"  # Context size
            ]
            
            # Execute the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45  # 45 second timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"llama.cpp error: {result.stderr}")
                return self.generate_fallback_response()
                
        except subprocess.TimeoutExpired:
            logger.error("llama.cpp call timed out")
            return self.generate_fallback_response()
        except Exception as e:
            logger.error(f"Error calling llama.cpp: {e}")
            return self.generate_fallback_response()
    
    def generate_fallback_response(self) -> str:
        """
        Generates a fallback response when llama.cpp is unavailable
        """
        word = random.choice(self.common_words)
        return f"I guess {word}. Using fallback strategy as my AI system is having issues."
    
    def extract_word_from_response(self, raw_response: str) -> Dict[str, str]:
        """
        Extracts a 5-letter word from the LLM response using multiple strategies
        Priority: GUESS: format > other patterns > fallback
        """
        try:
            # Strategy 1: Look for GUESS: format (highest priority)
            guess_pattern = r'GUESS:\s*([A-Z]{5})'
            guess_match = re.search(guess_pattern, raw_response, re.IGNORECASE)
            if guess_match:
                word = guess_match.group(1).upper().strip()
                if len(word) == 5 and word.isalpha():
                    return {
                        'word_guess': word,
                        'comments': raw_response,
                        'raw_response': raw_response,
                        'parsing_method': 'GUESS: format'
                    }
            
            # Strategy 2: Look for JSON format
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    if 'word_guess' in parsed:
                        word = str(parsed['word_guess']).upper().strip()
                        if len(word) == 5 and word.isalpha():
                            return {
                                'word_guess': word,
                                'comments': parsed.get('comments', raw_response),
                                'raw_response': raw_response,
                                'parsing_method': 'JSON format'
                            }
                except json.JSONDecodeError:
                    pass
            
            # Strategy 3: Look for other common patterns
            patterns = [
                r'(?:I guess|My guess|I choose|I pick|I think|I\'ll try|I\'ll guess)\s*:?\s*([A-Z]{5})',
                r'([A-Z]{5})\s*(?:is my guess|is my choice|is my pick)',
                r'(?:word|answer)\s*:?\s*([A-Z]{5})'
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, raw_response, re.IGNORECASE)
                for match in matches:
                    word = match.upper().strip()
                    if len(word) == 5 and word.isalpha():
                        return {
                            'word_guess': word,
                            'comments': raw_response,
                            'raw_response': raw_response,
                            'parsing_method': f'Pattern {i+1}'
                        }
            
            # Strategy 4: Fallback - ask for retry
            logger.warning(f"Could not extract valid word from: {raw_response}")
            return {
                'word_guess': 'RETRY',
                'comments': f"Please use the format 'GUESS: YOURWORD'. Your response: {raw_response[:100]}...",
                'raw_response': raw_response,
                'parsing_method': 'RETRY - no valid format found'
            }
            
        except Exception as e:
            logger.error(f"Error extracting word from response: {e}")
            fallback_word = random.choice(self.common_words)
            return {
                'word_guess': fallback_word,
                'comments': f"Error processing response, using fallback guess {fallback_word}.",
                'raw_response': raw_response,
                'parsing_method': 'ERROR - fallback used'
            }
    
    def get_guess(self, game_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Main method to get a word guess from the LLM
        """
        logger.info(f"{self.player_name} generating guess for turn {game_data.get('turn_number', 1)}")
        
        # Construct the prompt
        prompt = self.construct_prompt(game_data)
        
        # Call llama.cpp
        raw_response = self.call_llama_cpp(prompt)
        
        # Extract word and comments
        parsed_response = self.extract_word_from_response(raw_response)
        
        logger.info(f"{self.player_name} generated guess: {parsed_response['word_guess']}")
        return parsed_response

# Initialize the player
player = WordlePlayer("Player 1")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "player1_server", "player": "Player 1"})

@app.route('/get_guess', methods=['POST'])
def get_guess():
    """
    Main endpoint for getting word guesses
    Expects JSON with game state information
    Returns JSON with word_guess and comments
    """
    try:
        # Get the game data from the request
        game_data = request.get_json()
        
        if not game_data:
            return jsonify({"error": "No game data provided"}), 400
        
        # Generate the guess
        response = player.get_guess(game_data)
        
        # Log the interaction
        logger.info(f"Request: {game_data}")
        logger.info(f"Response: {response}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in get_guess endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/', methods=['GET'])
def index():
    """Simple index page for testing"""
    return f"""
    <h1>LLM Wordle Player 1 Server</h1>
    <p>This server provides word guessing functionality for Player 1 in the LLM Wordle game.</p>
    <p>Player: {player.player_name}</p>
    <p>Send POST requests to /get_guess with game state data.</p>
    <p>Health check: <a href="/health">/health</a></p>
    """

if __name__ == '__main__':
    # Check if llama.cpp is available
    if not os.path.exists(player.llama_cpp_path):
        logger.warning(f"llama.cpp not found at {player.llama_cpp_path}")
        logger.warning("Server will use fallback responses")
    
    if not os.path.exists(player.model_path):
        logger.warning(f"Model not found at {player.model_path}")
        logger.warning("Server will use fallback responses")
    
    logger.info("Starting Player 1 Server on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
