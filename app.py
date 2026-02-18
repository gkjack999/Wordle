from flask import Flask, render_template, request, session, jsonify
from collections import defaultdict
import random
import uuid

app = Flask(__name__)
app.secret_key = "evil_secret_key"

WORD_LENGTH = 5
MAX_GUESSES = 6

# In-memory game store: game_id -> state
GAMES = {}


def load_word_list(filename):
    with open(filename) as f:
        return [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]


# Load word lists
answers = load_word_list("wordle-answers.txt")
guesses_extra = load_word_list("wordle-guesses.txt")

answers_set = set(answers)
ALL_WORDS = list(set(answers) | set(guesses_extra))
ALL_WORDS_SET = set(ALL_WORDS)


# ---------------------------
# Wordle scoring (correct duplicate handling)
# ---------------------------

def score_pattern(guess, answer):
    result = ["B"] * WORD_LENGTH
    answer_chars = list(answer)
    guess_chars = list(guess)

    # Greens
    for i in range(WORD_LENGTH):
        if guess_chars[i] == answer_chars[i]:
            result[i] = "G"
            answer_chars[i] = None
            guess_chars[i] = None

    # Yellows
    for i in range(WORD_LENGTH):
        if guess_chars[i] is not None and guess_chars[i] in answer_chars:
            result[i] = "Y"
            idx = answer_chars.index(guess_chars[i])
            answer_chars[idx] = None

    return "".join(result)


# ---------------------------
# Adversarial bucket selection
# ---------------------------

def choose_max_remaining_bucket(guess, candidates):
    buckets = defaultdict(list)

    for word in candidates:
        pattern = score_pattern(guess, word)
        buckets[pattern].append(word)

    max_size = max(len(group) for group in buckets.values())

    largest = [
        (pattern, group)
        for pattern, group in buckets.items()
        if len(group) == max_size
    ]

    # Random tie-break among equally large buckets
    return random.choice(largest)


# ---------------------------
# Final word selection (random sample from live universe)
# ---------------------------

def choose_final_word(candidates):
    if not candidates:
        return None

    remaining_answers = [w for w in candidates if w in answers_set]
    remaining_guesses = [w for w in candidates if w not in answers_set]

    if remaining_answers:
        return random.choice(remaining_answers)

    if remaining_guesses:
        return random.choice(remaining_guesses)

    return None


# ---------------------------
# Game state management
# ---------------------------

def new_game():
    game_id = str(uuid.uuid4())
    session["game_id"] = game_id
    GAMES[game_id] = {
        "candidates": ALL_WORDS.copy(),
        "guesses": [],
        "game_over": False,
    }
    return game_id, GAMES[game_id]


def get_game():
    game_id = session.get("game_id")
    if not game_id or game_id not in GAMES:
        return new_game()
    return game_id, GAMES[game_id]


# ---------------------------
# Routes
# ---------------------------

@app.route("/")
def index():
    new_game()
    return render_template("index.html")


@app.route("/guess", methods=["POST"])
def guess():
    game_id, game = get_game()

    if game["game_over"]:
        return jsonify({"error": "Game over"})

    guess_word = request.json.get("guess", "").lower().strip()

    if len(guess_word) != WORD_LENGTH:
        return jsonify({"error": "Guess must be 5 letters"})

    if guess_word not in ALL_WORDS_SET:
        return jsonify({"error": "Not in word list"})

    candidates = game["candidates"]

    pattern, new_candidates = choose_max_remaining_bucket(guess_word, candidates)

    game["candidates"] = new_candidates
    game["guesses"].append({"word": guess_word, "pattern": pattern})

    # End conditions
    if pattern == "GGGGG" or len(game["guesses"]) >= MAX_GUESSES:
        game["game_over"] = True
        final_word = choose_final_word(new_candidates)

        if final_word is None:
            final_word = guess_word  # safety fallback

        return jsonify({
            "pattern": pattern,
            "game_over": True,
            "final_word": final_word
        })

    return jsonify({
        "pattern": pattern,
        "game_over": False
    })


if __name__ == "__main__":
    # IMPORTANT: disable reloader to avoid dual-process memory bug
    app.run(debug=False, use_reloader=False)
