# LLM Wordle Project - Updated Changes Checklist

This checklist outlines the critical modifications you need to make in the provided code files to adapt them to your specific environment and LLM setup. The updated version includes enhanced format requirements for more reliable LLM parsing.

## 1. `player1_server.py` (Runs in WSL Ubuntu)

This file connects to your `llama.cpp` build and model. You **MUST** update the paths to your specific setup.

- **Locate:** `self.llama_cpp_path`
  - **Original:** `self.llama_cpp_path = "/path/to/llama.cpp/build/bin/llama-run"`
  - **Change to:** The absolute path to your `llama.cpp` executable. If you built with CMake, this is typically `llama.cpp/build/bin/llama-run` or `llama.cpp/build/bin/llama`.
  - **Example:** `self.llama_cpp_path = "/home/ubuntu/llama.cpp/build/bin/llama-run"`

- **Locate:** `self.model_path`
  - **Original:** `self.model_path = "/path/to/your/model.gguf"`
  - **Change to:** The absolute path to your downloaded GGUF model file.
  - **Example:** `self.model_path = "/home/ubuntu/models/llama-2-7b-chat.Q4_K_M.gguf"`

## 2. `player2_server.py` (Runs on Windows)

This file connects to your Ollama instance. Verify the URL and model name.

- **Locate:** `self.ollama_url`
  - **Original:** `self.ollama_url = "http://localhost:11434/api/generate"`
  - **Verify:** This is the default Ollama API endpoint. If your Ollama server is running on a different host or port, update this accordingly.

- **Locate:** `self.model_name`
  - **Original:** `self.model_name = "llama2"`
  - **Change to:** The name of the model you have pulled and want to use with Ollama (e.g., `"mistral"`, `"phi3"`). Ensure this model is available in your Ollama library (`ollama list`).

## 3. `referee_server.py` (Runs on Windows)

This file orchestrates the game and serves the web interface. Ensure the LLM server URLs are correct.

- **Locate:** `self.player1_url`
  - **Original:** `self.player1_url = "http://localhost:5001/get_guess"`
  - **Verify:** This should typically remain `localhost` as WSL automatically forwards requests from Windows. If you changed the port in `player1_server.py`, update it here.

- **Locate:** `self.player2_url`
  - **Original:** `self.player2_url = "http://localhost:5002/get_guess"`
  - **Verify:** This should typically remain `localhost`. If you changed the port in `player2_server.py`, update it here.

- **Locate:** `app.config["SECRET_KEY"]`
  - **Original:** `app.config["SECRET_KEY"] = "your-secret-key-here-change-this"`
  - **Change to:** A strong, random secret key. This is important for Flask session security.
  - **Example:** `app.config["SECRET_KEY"] = "super-secret-random-string-12345"`

## 4. `requirements.txt`

This file lists all Python dependencies. Ensure you install these in the correct virtual environments.

- **No direct changes needed in this file.**
- **Action:** Make sure to run `pip install -r requirements.txt` in the virtual environments for both Player servers and the Referee server as described in `SETUP_GUIDE.md`.

## New Features in This Version:

### Enhanced Format Requirements
Both player servers now require LLMs to use a specific format: `GUESS: YOURWORD`

**Example of expected LLM response:**
```
I think based on the feedback, the word might contain an 'A' and an 'E'. 
Let me try a common word with those letters.

GUESS: HOUSE

This seems like a reasonable guess given the constraints.
```

### Automatic Retry Logic
- If an LLM doesn't use the proper format, the system will automatically retry up to 2 times
- The retry includes a reminder message about the required format
- After 2 failed attempts, a fallback word is used

### Improved Parsing Priority
1. **GUESS: format** (highest priority)
2. **JSON format** (if provided)
3. **Common patterns** (I guess WORD, etc.)
4. **Fallback words** (if all else fails)

## Important Notes:

- **File Paths:** Always use absolute paths for `llama_cpp_path` and `model_path`.
- **Ollama Models:** Ensure the model you specify in `player2_server.py` is actually downloaded and available in Ollama.
- **Ports:** If you change any default ports (5000, 5001, 5002), ensure you update all corresponding URLs in the other server files.
- **Format Training:** You may want to test your LLMs with the `GUESS: WORD` format before running the full game to ensure they understand the requirement.

By following this checklist, you should be able to configure the project successfully for your environment with much more reliable LLM response parsing.

