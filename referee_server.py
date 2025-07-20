#!/usr/bin/env python3
"""
LLM Wordle Referee Server with Scripted Game Master
Orchestrates the game between two LLM players and serves the web interface
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import requests
import random
import logging
from logging.handlers import RotatingFileHandler
import threading
import time
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Create a dedicated logger for frontend events ---
frontend_logger = logging.getLogger('frontend_logger')
frontend_logger.setLevel(logging.DEBUG)
# Use a rotating file handler to prevent the log file from growing too large
fh = RotatingFileHandler('frontend_debug.log', maxBytes=1024*1024, backupCount=3, encoding='utf-8')
fh.setLevel(logging.DEBUG)
# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(message)s')
fh.setFormatter(formatter)
# Add the handler to the logger
frontend_logger.addHandler(fh)

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here-change-this"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class WordleGameMaster:
    """
    Scripted Game Master that handles all Wordle game logic deterministically
    """
    
    def __init__(self):
        # Common 5-letter Wordle words
        self.word_list = [
            "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT", "ADULT", "AFTER", "AGAIN",
            "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT", "ALIEN", "ALIGN", "ALIKE", "ALIVE",
            "ALLOW", "ALONE", "ALONG", "ALTER", "ANGEL", "ANGER", "ANGLE", "ANGRY", "APART", "APPLE",
            "APPLY", "ARENA", "ARGUE", "ARISE", "ARRAY", "ASIDE", "ASSET", "AUDIO", "AUDIT", "AVOID",
            "AWAKE", "AWARD", "AWARE", "BADLY", "BAKER", "BASES", "BASIC", "BEACH", "BEGAN", "BEGIN",
            "BEING", "BELOW", "BENCH", "BILLY", "BIRTH", "BLACK", "BLAME", "BLANK", "BLAST", "BLIND",
            "BLOCK", "BLOOD", "BOARD", "BOAST", "BOATS", "BOBBY", "BONDS", "BOOST", "BOOTH", "BOUND",
            "BRAIN", "BRAND", "BRASS", "BRAVE", "BREAD", "BREAK", "BREED", "BRIEF", "BRING", "BROAD",
            "BROKE", "BROWN", "BUILD", "BUILT", "BUYER", "CABLE", "CALIF", "CARRY", "CATCH", "CAUSE",
            "CHAIN", "CHAIR", "CHAOS", "CHARM", "CHART", "CHASE", "CHEAP", "CHECK", "CHEST", "CHIEF",
            "CHILD", "CHINA", "CHOSE", "CIVIL", "CLAIM", "CLASS", "CLEAN", "CLEAR", "CLICK", "CLIMB",
            "CLOCK", "CLOSE", "CLOUD", "COACH", "COAST", "COULD", "COUNT", "COURT", "COVER", "CRAFT",
            "CRANE", "CRASH", "CRAZY", "CREAM", "CRIME", "CROSS", "CROWD", "CROWN", "CRUDE", "CURVE",
            "CYCLE", "DAILY", "DANCE", "DATED", "DEALT", "DEATH", "DEBUT", "DELAY", "DEPTH", "DOING",
            "DOUBT", "DOZEN", "DRAFT", "DRAMA", "DRANK", "DREAM", "DRESS", "DRILL", "DRINK", "DRIVE",
            "DROVE", "DYING", "EAGER", "EARLY", "EARTH", "EIGHT", "ELITE", "EMPTY", "ENEMY", "ENJOY",
            "ENTER", "ENTRY", "EQUAL", "ERROR", "EVENT", "EVERY", "EXACT", "EXIST", "EXTRA", "FAITH",
            "FALSE", "FAULT", "FIBER", "FIELD", "FIFTH", "FIFTY", "FIGHT", "FINAL", "FIRST", "FIXED",
            "FLASH", "FLEET", "FLOOR", "FLUID", "FOCUS", "FORCE", "FORTH", "FORTY", "FORUM", "FOUND",
            "FRAME", "FRANK", "FRAUD", "FRESH", "FRONT", "FRUIT", "FULLY", "FUNNY", "GIANT", "GIVEN",
            "GLASS", "GLOBE", "GOING", "GRACE", "GRADE", "GRAND", "GRANT", "GRASS", "GRAVE", "GREAT",
            "GREEN", "GROSS", "GROUP", "GROWN", "GUARD", "GUESS", "GUEST", "GUIDE", "HAPPY", "HARRY",
            "HEART", "HEAVY", "HENCE", "HENRY", "HORSE", "HOTEL", "HOUSE", "HUMAN", "IDEAL", "IMAGE",
            "INDEX", "INNER", "INPUT", "ISSUE", "JAPAN", "JIMMY", "JOINT", "JONES", "JUDGE", "KNOWN",
            "LABEL", "LARGE", "LASER", "LATER", "LAUGH", "LAYER", "LEARN", "LEASE", "LEAST", "LEAVE",
            "LEGAL", "LEVEL", "LEWIS", "LIGHT", "LIMIT", "LINKS", "LIVES", "LOCAL", "LOOSE", "LOWER",
            "LUCKY", "LUNCH", "LYING", "MAGIC", "MAJOR", "MAKER", "MARCH", "MARIA", "MATCH", "MAYBE",
            "MAYOR", "MEANT", "MEDIA", "METAL", "MIGHT", "MINOR", "MINUS", "MIXED", "MODEL", "MONEY",
            "MONTH", "MORAL", "MOTOR", "MOUNT", "MOUSE", "MOUTH", "MOVED", "MOVIE", "MUSIC", "NEEDS",
            "NEVER", "NEWLY", "NIGHT", "NOISE", "NORTH", "NOTED", "NOVEL", "NURSE", "OCCUR", "OCEAN",
            "OFFER", "OFTEN", "ORDER", "OTHER", "OUGHT", "PAINT", "PANEL", "PAPER", "PARTY", "PEACE",
            "PETER", "PHASE", "PHONE", "PHOTO", "PIANO", "PICKED", "PIECE", "PILOT", "PITCH", "PLACE",
            "PLAIN", "PLANE", "PLANT", "PLATE", "POINT", "POUND", "POWER", "PRESS", "PRICE", "PRIDE",
            "PRIME", "PRINT", "PRIOR", "PRIZE", "PROOF", "PROUD", "PROVE", "QUEEN", "QUICK", "QUIET",
            "QUITE", "RADIO", "RAISE", "RANGE", "RAPID", "RATIO", "REACH", "READY", "REALM", "REBEL",
            "REFER", "RELAX", "REPAY", "REPLY", "RIGHT", "RIGID", "RIVAL", "RIVER", "ROBIN", "ROGER",
            "ROMAN", "ROUGH", "ROUND", "ROUTE", "ROYAL", "RURAL", "SCALE", "SCENE", "SCOPE", "SCORE",
            "SENSE", "SERVE", "SEVEN", "SHALL", "SHAPE", "SHARE", "SHARP", "SHEET", "SHELF", "SHELL",
            "SHIFT", "SHINE", "SHIRT", "SHOCK", "SHOOT", "SHORT", "SHOWN", "SIGHT", "SILLY", "SINCE",
            "SIXTH", "SIXTY", "SIZED", "SKILL", "SLEEP", "SLIDE", "SMALL", "SMART", "SMILE", "SMITH",
            "SMOKE", "SOLID", "SOLVE", "SORRY", "SOUND", "SOUTH", "SPACE", "SPARE", "SPEAK", "SPEED",
            "SPEND", "SPENT", "SPLIT", "SPOKE", "SPORT", "STAFF", "STAGE", "STAKE", "STAND", "START",
            "STATE", "STEAM", "STEEL", "STEEP", "STEER", "STICK", "STILL", "STOCK", "STONE", "STOOD",
            "STORE", "STORM", "STORY", "STRIP", "STUCK", "STUDY", "STUFF", "STYLE", "SUGAR", "SUITE",
            "SUPER", "SWEET", "TABLE", "TAKEN", "TASTE", "TAXES", "TEACH", "TEAMS", "TEETH", "TERRY",
            "TEXAS", "THANK", "THEFT", "THEIR", "THEME", "THERE", "THESE", "THICK", "THING", "THINK",
            "THIRD", "THOSE", "THREE", "THREW", "THROW", "THUMB", "TIGHT", "TIRED", "TITLE", "TODAY",
            "TOPIC", "TOTAL", "TOUCH", "TOUGH", "TOWER", "TRACK", "TRADE", "TRAIN", "TREAT", "TREND",
            "TRIAL", "TRIBE", "TRICK", "TRIED", "TRIES", "TRUCK", "TRULY", "TRUNK", "TRUST", "TRUTH",
            "TWICE", "UNCLE", "UNDUE", "UNION", "UNITY", "UNTIL", "UPPER", "UPSET", "URBAN", "USAGE",
            "USUAL", "VALID", "VALUE", "VIDEO", "VIRUS", "VISIT", "VITAL", "VOCAL", "VOICE", "WASTE",
            "WATCH", "WATER", "WHEEL", "WHERE", "WHICH", "WHILE", "WHITE", "WHOLE", "WHOSE", "WOMAN",
            "WOMEN", "WORLD", "WORRY", "WORSE", "WORST", "WORTH", "WOULD", "WRITE", "WRONG", "WROTE",
            "YOUNG", "YOUTH"
        ]
    
    def choose_secret_word(self) -> str:
        """Choose a random secret word for the game"""
        return random.choice(self.word_list)
    
    def evaluate_guess(self, guess: str, secret_word: str) -> str:
        """
        Evaluates a guess against the secret word and returns emoji feedback
        🟩 = correct letter in correct position
        🟨 = correct letter in wrong position
        ⬜ = letter not in word
        """
        if len(guess) != 5 or len(secret_word) != 5:
            return "⬜⬜⬜⬜⬜"  # Invalid guess
        
        guess = guess.upper()
        secret_word = secret_word.upper()
        
        feedback = ['⬜'] * 5
        secret_chars = list(secret_word)
        
        # First pass: mark exact matches
        for i in range(5):
            if guess[i] == secret_word[i]:
                feedback[i] = '🟩'
                secret_chars[i] = None  # Mark as used
        
        # Second pass: mark partial matches
        for i in range(5):
            if feedback[i] == '⬜' and guess[i] in secret_chars:
                feedback[i] = '🟨'
                # Remove the first occurrence of this character
                secret_chars[secret_chars.index(guess[i])] = None
        
        return ''.join(feedback)
    def is_valid_word(self, word: str) -> bool:
        """Check if a word is valid (5 letters, alphabetic)"""
        return len(word) == 5 and word.isalpha() and word.upper() in self.word_list

class WordleReferee:
    """
    Main game orchestrator that manages the competition between two LLM players
    """
    
    def __init__(self):
        self.game_master = WordleGameMaster()
        self.player1_url = "http://localhost:5001/get_guess"
        self.player2_url = "http://localhost:5002/get_guess"
        self.request_timeout = 120  # Timeout in seconds for player requests
        
        # Game state
        self.reset_game()
    
    def reset_game(self):
        """Reset the game state for a new game"""
        self.secret_word = None
        self.current_turn = 0
        self.max_turns = 6
        self.game_over = False
        self.winner = None
        self.player1_history = []
        self.player2_history = []
        self.game_log = []
    
    def start_new_game(self):
        """Start a new game"""
        self.reset_game()
        self.secret_word = self.game_master.choose_secret_word()
        logger.info(f"New game started with secret word: {self.secret_word}")
        
        # Emit game started event
        socketio.emit('game_started', {
            'secret_word': '[HIDDEN]',
            'max_turns': self.max_turns,
            'status': 'Game started! Both players will compete to guess the word.'
        })
        
        return True
    
    def get_player_guess(self, player_url: str, player_name: str, history: List[Dict]) -> Optional[Dict[str, str]]:
        """Get a guess from a player LLM with retry logic for format errors"""
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                game_data = {
                    'turn_number': self.current_turn,
                    'max_turns': self.max_turns,
                    'history': history,
                    'player_message': f'You are competing against another AI player. Good luck!'
                }
                
                # Add retry message if this is a retry attempt
                if attempt > 0:
                    game_data['player_message'] += f' [RETRY {attempt}/{max_retries}] Please use the format: GUESS: YOURWORD'
                
                response = requests.post(player_url, json=game_data, timeout=self.request_timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check if we got a RETRY response
                    if result.get('word_guess') == 'RETRY':
                        if attempt < max_retries:
                            logger.warning(f"{player_name} returned RETRY, attempting retry {attempt + 1}")
                            continue
                        else:
                            logger.error(f"{player_name} failed after {max_retries} retries, using fallback")
                            # Use a fallback word
                            fallback_words = ["AUDIO", "CRANE", "SLATE", "ROAST", "PLANT"]
                            result['word_guess'] = random.choice(fallback_words)
                            result['comments'] = f"Failed to provide proper format after {max_retries} retries. Using fallback word."
                    
                    return result
                else:
                    logger.error(f"Error from {player_name}: {response.status_code}")
                    if attempt < max_retries:
                        continue
                    return None
                    
            except Exception as e:
                logger.error(f"Error getting guess from {player_name} (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    continue
                return None
        
        return None
    
    def process_turn(self):
        """Process one turn of the game for both players"""
        if self.game_over:
            return
        
        self.current_turn += 1
        
        # Emit status update
        socketio.emit('status_update', {
            'turn': self.current_turn,
            'max_turns': self.max_turns,
            'status': f'Turn {self.current_turn}: Getting guesses from both players...'
        })
        
        # Get guesses from both players simultaneously
        player1_response = self.get_player_guess(self.player1_url, "Player 1", self.player1_history)
        player2_response = self.get_player_guess(self.player2_url, "Player 2", self.player2_history)
        
        # Process Player 1
        if player1_response:
            guess1 = player1_response.get('word_guess', '').upper()
            comments1 = player1_response.get('comments', '')
            raw_response1 = player1_response.get('raw_response', '')
            parsing_method1 = player1_response.get('parsing_method', 'Unknown')
            feedback1 = self.game_master.evaluate_guess(guess1, self.secret_word)
            
            self.player1_history.append({
                'guess': guess1,
                'feedback': feedback1
            })
            
            # Emit Player 1 turn
            socketio.emit('player_turn', {
                'player': 'Player 1',
                'turn': self.current_turn,
                'guess': guess1,
                'feedback': feedback1,
                'comments': comments1,
                'raw_response': raw_response1,
                'parsing_method': parsing_method1
            })
            
            # Check if Player 1 won
            if feedback1 == '🟩🟩🟩🟩🟩':
                self.game_over = True
                self.winner = 'Player 1'
        
        # Process Player 2
        if player2_response:
            guess2 = player2_response.get('word_guess', '').upper()
            comments2 = player2_response.get('comments', '')
            raw_response2 = player2_response.get('raw_response', '')
            parsing_method2 = player2_response.get('parsing_method', 'Unknown')
            feedback2 = self.game_master.evaluate_guess(guess2, self.secret_word)
            
            self.player2_history.append({
                'guess': guess2,
                'feedback': feedback2
            })
            
            # Emit Player 2 turn
            socketio.emit('player_turn', {
                'player': 'Player 2',
                'turn': self.current_turn,
                'guess': guess2,
                'feedback': feedback2,
                'comments': comments2,
                'raw_response': raw_response2,
                'parsing_method': parsing_method2
            })
            
            # Check if Player 2 won
            if feedback2 == '🟩🟩🟩🟩🟩':
                if self.winner == 'Player 1':
                    self.winner = 'Tie'  # Both guessed correctly on same turn
                else:
                    self.game_over = True
                    self.winner = 'Player 2'
        
        # Check if game should end
        if self.current_turn >= self.max_turns:
            self.game_over = True
            if not self.winner:
                self.winner = 'No winner'
        
        # Emit game finished if over
        if self.game_over:
            socketio.emit('game_finished', {
                'winner': self.winner,
                'secret_word': self.secret_word,
                'total_turns': self.current_turn,
                'player1_history': self.player1_history,
                'player2_history': self.player2_history
            })
    
    def run_game_loop(self):
        """Run the main game loop in a separate thread"""
        while not self.game_over and self.current_turn < self.max_turns:
            self.process_turn()
            time.sleep(2)  # Brief pause between turns

# Initialize the referee
referee = WordleReferee()

@app.route('/')
def index():
    """Serve the main game interface"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "referee_server"})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connected', {'status': 'Connected to LLM Wordle Battle server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('log_event')
def handle_log_event(data):
    """Handle log events from the frontend and write to a file"""
    message = data.get('message', 'No message content')
    frontend_logger.info(message)

@socketio.on('start_game')
def handle_start_game():
    """Handle start game request"""
    logger.info('Starting new game')
    
    if referee.start_new_game():
        # Start the game loop in a separate thread
        game_thread = threading.Thread(target=referee.run_game_loop)
        game_thread.daemon = True
        game_thread.start()
    else:
        emit('error', {'message': 'Failed to start game'})

if __name__ == '__main__':
    logger.info("Starting Referee Server on port 5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
