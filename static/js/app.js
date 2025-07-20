/**
 * LLM Wordle Battle - Frontend JavaScript Application
 * Handles WebSocket communication and UI updates for two-player competition
 */

class WordleBattle {
    constructor() {
        this.socket = null;
        this.gameState = {
            started: false,
            over: false,
            winner: null,
            currentTurn: 0,
            maxTurns: 6,
            secretWord: null,
            player1Grid: [],
            player2Grid: []
        };
        
        this.initializeGrids();
        this.initializeSocket();
        this.bindEvents();
    }
    
    initializeGrids() {
        // Initialize Player 1 grid
        const grid1 = document.getElementById('player1-grid');
        grid1.innerHTML = '';
        
        // Initialize Player 2 grid
        const grid2 = document.getElementById('player2-grid');
        grid2.innerHTML = '';
        
        // Create 6 rows of 5 cells each for both players
        for (let row = 0; row < 6; row++) {
            for (let col = 0; col < 5; col++) {
                // Player 1 cell
                const cell1 = document.createElement('div');
                cell1.className = 'grid-cell';
                cell1.id = `p1-cell-${row}-${col}`;
                grid1.appendChild(cell1);
                
                // Player 2 cell
                const cell2 = document.createElement('div');
                cell2.className = 'grid-cell';
                cell2.id = `p2-cell-${row}-${col}`;
                grid2.appendChild(cell2);
            }
        }
        
        // Initialize grid state
        this.gameState.player1Grid = Array(6).fill().map(() => Array(5).fill(''));
        this.gameState.player2Grid = Array(6).fill().map(() => Array(5).fill(''));
    }
    
    initializeSocket() {
        this.socket = io();
        
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateStatus('Connected to server');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateStatus('Disconnected from server');
        });
        
        this.socket.on('connected', (data) => {
            console.log('Server confirmation:', data);
            this.addLogMessage('system', 'System', data.status);
        });
        
        // Game events
        this.socket.on('game_started', (data) => {
            this.handleGameStarted(data);
        });
        
        this.socket.on('status_update', (data) => {
            this.handleStatusUpdate(data);
        });
        
        this.socket.on('player_turn', (data) => {
            this.handlePlayerTurn(data);
        });
        
        this.socket.on('game_finished', (data) => {
            this.handleGameFinished(data);
        });
        
        this.socket.on('error', (data) => {
            this.handleError(data);
        });
    }
    
    bindEvents() {
        const startBtn = document.getElementById('start-game-btn');
        const newGameBtn = document.getElementById('new-game-btn');
        const celebrateBtn = document.getElementById('celebrate-btn');
        
        startBtn.addEventListener('click', () => {
            this.startGame();
        });
        
        newGameBtn.addEventListener('click', () => {
            this.resetGame();
        });
        
        celebrateBtn.addEventListener('click', () => {
            this.hideWinnerAnnouncement();
        });
    }
    
    startGame() {
        console.log('Starting new battle...');
        this.showLoading('Starting AI battle...');
        this.socket.emit('start_game');
        
        // Disable start button
        const startBtn = document.getElementById('start-game-btn');
        startBtn.disabled = true;
        startBtn.style.display = 'none';
        
        // Update player statuses
        this.updatePlayerStatus('player1', 'Preparing...', 'thinking');
        this.updatePlayerStatus('player2', 'Preparing...', 'thinking');
    }
    
    resetGame() {
        console.log('Resetting battle...');
        
        // Reset game state
        this.gameState = {
            started: false,
            over: false,
            winner: null,
            currentTurn: 0,
            maxTurns: 6,
            secretWord: null,
            player1Grid: [],
            player2Grid: []
        };
        
        // Reset UI
        this.initializeGrids();
        this.updateTurnCounter(0, 6);
        this.updateStatus('Ready to Start');
        this.updateSecretWord('[Hidden]');
        
        // Reset buttons
        const startBtn = document.getElementById('start-game-btn');
        const newGameBtn = document.getElementById('new-game-btn');
        
        startBtn.disabled = false;
        startBtn.style.display = 'inline-block';
        newGameBtn.style.display = 'none';
        
        // Reset player statuses
        this.updatePlayerStatus('player1', 'Waiting...', '');
        this.updatePlayerStatus('player2', 'Waiting...', '');
        
        // Clear battle log except system message
        const log = document.getElementById('battle-log');
        log.innerHTML = `
            <div class="log-message system">
                <span class="message-sender">System:</span>
                <span class="message-content">Welcome to LLM Wordle Battle! Click "Start Battle" to watch two AI models compete.</span>
            </div>
        `;
        
        this.hideLoading();
        this.hideWinnerAnnouncement();
    }
    
    handleGameStarted(data) {
        console.log('Battle started:', data);
        this.gameState.started = true;
        this.gameState.maxTurns = data.max_turns;
        
        this.updateTurnCounter(0, data.max_turns);
        this.updateStatus('Battle in progress!');
        this.addLogMessage('system', 'System', data.status);
        
        this.hideLoading();
    }
    
    handleStatusUpdate(data) {
        console.log('Status update:', data);
        this.updateStatus(data.status);
        this.updateTurnCounter(data.turn, data.max_turns);
        
        // Update player statuses based on current activity
        if (data.status.includes('Getting guesses')) {
            this.updatePlayerStatus('player1', 'Thinking...', 'thinking');
            this.updatePlayerStatus('player2', 'Thinking...', 'thinking');
        }
    }
    
    handlePlayerTurn(data) {
        console.log('Player turn:', data);
        
        const player = data.player;
        const guess = data.guess.toUpperCase();
        const feedback = data.feedback;
        console.log(`Complete feedback received for ${player}:`, feedback); // Log the entire feedback string

        const feedbackChars = Array.from(feedback); // Correctly handle multi-byte emoji characters
        const turn = data.turn - 1; // Convert to 0-based index
        const comments = data.comments;
        const rawResponse = data.raw_response || '';
        const parsingMethod = data.parsing_method || 'Unknown';
        
        // Determine player prefix and grid
        const playerPrefix = player === 'Player 1' ? 'p1' : 'p2';
        const playerNum = player === 'Player 1' ? 'player1' : 'player2';
        
        // Update grid with player's guess
        for (let i = 0; i < 5; i++) {
            const cell = document.getElementById(`${playerPrefix}-cell-${turn}-${i}`);
            cell.textContent = guess[i];
            cell.classList.add('filled');
            
            // Add feedback colors with animation delay
            setTimeout(() => {
                const feedbackChar = feedbackChars[i]; // Use the correctly parsed emoji character
                console.log("Feedback Char:", feedbackChar);  // Log the feedback character
                // Send the feedback character to the server for logging
                this.socket.emit('log_event', { message: `[Turn ${data.turn}] [Player: ${player}] Processing feedback char: ${feedbackChar}` });
                switch (feedbackChar) {
                    case '🟩':
                        cell.classList.add('correct');
                        break;
                    case '🟨':
                        cell.classList.add('present');
                        break;
                    case '⬜':
                        cell.classList.add('absent');
                        break;
                }
            }, (i + 1) * 200);
        }
        
        // Update game state
        if (player === 'Player 1') {
            this.gameState.player1Grid[turn] = guess.split('');
        } else {
            this.gameState.player2Grid[turn] = guess.split('');
        }
        
        this.gameState.currentTurn = data.turn;
        
        // Create detailed log message with raw response
        const logClass = player === 'Player 1' ? 'player1' : 'player2';
        let logMessage = `Turn ${data.turn}: "${guess}" → ${feedback}`;
        
        // Add parsing method info if not standard
        if (parsingMethod !== 'GUESS: format') {
            logMessage += ` [Parsed via: ${parsingMethod}]`;
        }
        
        // Add comments if available
        if (comments && comments !== rawResponse) {
            logMessage += ` | ${comments}`;
        }
        
        this.addLogMessage(logClass, player, logMessage);
        
        // Add raw response as a separate collapsible entry for debugging
        if (rawResponse && rawResponse.trim()) {
            this.addRawResponseLog(logClass, player, rawResponse, parsingMethod);
        }
        
        // Update player status
        if (feedback === '🟩🟩🟩🟩🟩') {
            this.updatePlayerStatus(playerNum, 'WINNER! 🎉', 'winner');
        } else {
            this.updatePlayerStatus(playerNum, `Guessed: ${guess}`, '');
        }
    }
    
    handleGameFinished(data) {
        console.log('Battle finished:', data);
        
        this.gameState.over = true;
        this.gameState.winner = data.winner;
        this.gameState.secretWord = data.secret_word;
        
        // Update secret word display
        this.updateSecretWord(data.secret_word);
        
        // Update final status
        let statusMessage = '';
        let winnerMessage = '';
        let winnerDetails = '';
        
        switch (data.winner) {
            case 'Player 1':
                statusMessage = '🎉 Player 1 Wins!';
                winnerMessage = '🔵 Player 1 Wins!';
                winnerDetails = `Player 1 (llama.cpp) successfully guessed "${data.secret_word}" in ${data.total_turns} turns!`;
                this.updatePlayerStatus('player1', 'WINNER! 🎉', 'winner');
                this.updatePlayerStatus('player2', 'Good try!', 'loser');
                break;
            case 'Player 2':
                statusMessage = '🎉 Player 2 Wins!';
                winnerMessage = '🔴 Player 2 Wins!';
                winnerDetails = `Player 2 (Ollama) successfully guessed "${data.secret_word}" in ${data.total_turns} turns!`;
                this.updatePlayerStatus('player1', 'Good try!', 'loser');
                this.updatePlayerStatus('player2', 'WINNER! 🎉', 'winner');
                break;
            case 'Tie':
                statusMessage = '🤝 It\'s a Tie!';
                winnerMessage = '🤝 It\'s a Tie!';
                winnerDetails = `Both players guessed "${data.secret_word}" on turn ${data.total_turns}!`;
                this.updatePlayerStatus('player1', 'TIE! 🤝', 'winner');
                this.updatePlayerStatus('player2', 'TIE! 🤝', 'winner');
                break;
            default:
                statusMessage = '😔 No Winner';
                winnerMessage = '😔 No Winner';
                winnerDetails = `Neither player could guess "${data.secret_word}" in ${data.total_turns} turns.`;
                this.updatePlayerStatus('player1', 'No luck this time', 'loser');
                this.updatePlayerStatus('player2', 'No luck this time', 'loser');
                break;
        }
        
        this.updateStatus(statusMessage);
        this.addLogMessage('winner', 'Battle Result', winnerDetails);
        
        // Show winner announcement
        this.showWinnerAnnouncement(winnerMessage, winnerDetails);
        
        // Show new game button
        const newGameBtn = document.getElementById('new-game-btn');
        newGameBtn.style.display = 'inline-block';
        
        // Add celebration effect for wins
        if (data.winner !== 'No winner') {
            this.celebrateWin();
        }
    }
    
    handleError(data) {
        console.error('Battle error:', data);
        this.addLogMessage('system', 'Error', data.message);
        this.updateStatus('Error occurred');
        this.hideLoading();
        
        // Re-enable start button if game hasn't started
        if (!this.gameState.started) {
            const startBtn = document.getElementById('start-game-btn');
            startBtn.disabled = false;
            startBtn.style.display = 'inline-block';
        }
    }
    
    updateStatus(status) {
        const statusElement = document.getElementById('game-status');
        statusElement.textContent = status;
    }
    
    updateTurnCounter(current, max) {
        const counterElement = document.getElementById('turn-counter');
        counterElement.textContent = `${current}/${max}`;
    }
    
    updateSecretWord(word) {
        const secretElement = document.getElementById('secret-word');
        secretElement.textContent = word;
    }
    
    updatePlayerStatus(player, status, className) {
        const statusElement = document.getElementById(`${player}-status`);
        statusElement.textContent = status;
        statusElement.className = `player-status-text ${className}`;
    }
    
    addLogMessage(type, sender, content) {
        const log = document.getElementById('battle-log');
        const messageDiv = document.createElement('div');
        messageDiv.className = `log-message ${type}`;
        
        messageDiv.innerHTML = `
            <span class="message-sender">${sender}:</span>
            <span class="message-content">${content}</span>
        `;
        
        log.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        log.scrollTop = log.scrollHeight;
    }
    
    addRawResponseLog(type, sender, rawResponse, parsingMethod) {
        const log = document.getElementById('battle-log');
        const messageDiv = document.createElement('div');
        messageDiv.className = `log-message ${type} raw-response`;
        
        // Create collapsible raw response
        const responseId = `raw-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        messageDiv.innerHTML = `
            <div class="raw-response-header" onclick="this.parentElement.classList.toggle('expanded')">
                <span class="message-sender">${sender} Raw Response:</span>
                <span class="parsing-method">[${parsingMethod}]</span>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="raw-response-content">
                <pre>${rawResponse}</pre>
            </div>
        `;
        
        log.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        log.scrollTop = log.scrollHeight;
    }
    
    showLoading(text = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = overlay.querySelector('.loading-text');
        loadingText.textContent = text;
        overlay.style.display = 'flex';
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = 'none';
    }
    
    showWinnerAnnouncement(winnerText, details) {
        const announcement = document.getElementById('winner-announcement');
        const winnerTextElement = document.getElementById('winner-text');
        const winnerDetailsElement = document.getElementById('winner-details');
        
        winnerTextElement.textContent = winnerText;
        winnerDetailsElement.textContent = details;
        announcement.style.display = 'flex';
    }
    
    hideWinnerAnnouncement() {
        const announcement = document.getElementById('winner-announcement');
        announcement.style.display = 'none';
    }
    
    celebrateWin() {
        // Create floating emojis
        const emojis = ['🎉', '🎊', '🏆', '⭐', '🌟', '🎯', '🔥', '💫'];
        for (let i = 0; i < 15; i++) {
            setTimeout(() => {
                this.createFloatingEmoji(emojis[Math.floor(Math.random() * emojis.length)]);
            }, i * 150);
        }
    }
    
    createFloatingEmoji(emoji) {
        const emojiElement = document.createElement('div');
        emojiElement.textContent = emoji;
        emojiElement.style.cssText = `
            position: fixed;
            font-size: 2rem;
            pointer-events: none;
            z-index: 1000;
            left: ${Math.random() * window.innerWidth}px;
            top: ${window.innerHeight}px;
            animation: floatUp 4s ease-out forwards;
        `;
        
        document.body.appendChild(emojiElement);
        
        // Remove after animation
        setTimeout(() => {
            emojiElement.remove();
        }, 4000);
    }
}

// Add floating animation CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes floatUp {
        0% {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
        }
        100% {
            transform: translateY(-120vh) rotate(360deg);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize the battle when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing LLM Wordle Battle...');
    new WordleBattle();
});
