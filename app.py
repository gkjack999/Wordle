from flask import Flask, render_template, request, session, jsonify
from collections import defaultdict
import random
import uuid
import datetime

app = Flask(__name__)
app.secret_key = "evil_secret_key"

WORD_LENGTH = 5
MAX_GUESSES = 6

GAMES = {}


def load_word_list(filename):
    with open(filename) as f:
        return [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]


answers = load_word_list("wordle-answers.txt")
guesses_extra = load_word_list("wordle-guesses.txt")

answers_set = set(answers)
ALL_WORDS = list(set(answers) | set(guesses_extra))
ALL_WORDS_SET = set(ALL_WORDS)


# ---------------------------
# Wordle scoring
# ---------------------------

def score_pattern(guess, answer):
    result = ["B"] * WORD_LENGTH
    answer_chars = list(answer)
    guess_chars = list(guess)

    for i in range(WORD_LENGTH):
        if guess_chars[i] == answer_chars[i]:
            result[i] = "G"
            answer_chars[i] = None
            guess_chars[i] = None

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

    return random.choice(largest)


# ---------------------------
# Deterministic daily word
# ---------------------------

def get_daily_word(word_list):
    today_index = datetime.date.today().toordinal()
    return word_list[today_index % len(word_list)]


# ---------------------------
# Game state
# ---------------------------

def new_game(mode="hard"):
    game_id = str(uuid.uuid4())
    session["game_id"] = game_id

    if mode in ["easy", "daily_easy"]:
        candidates = answers.copy()
    else:
        candidates = ALL_WORDS.copy()

    state = {
        "mode": mode,
        "candidates": candidates,
        "guesses": [],
        "game_over": False,
    }

    # Auto-play daily first word
    if mode == "daily_easy":
        start_word = get_daily_word(answers)
        pattern, new_candidates = choose_max_remaining_bucket(start_word, candidates)
        state["candidates"] = new_candidates
        state["guesses"].append({"word": start_word, "pattern": pattern})

    if mode == "daily_hard":
        start_word = get_daily_word(ALL_WORDS)
        pattern, new_candidates = choose_max_remaining_bucket(start_word, candidates)
        state["candidates"] = new_candidates
        state["guesses"].append({"word": start_word, "pattern": pattern})

    GAMES[game_id] = state
    return game_id, state


def get_game():
    game_id = session.get("game_id")
    if not game_id or game_id not in GAMES:
        return new_game("hard")
    return game_id, GAMES[game_id]


# ---------------------------
# Routes
# ---------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/new_game", methods=["POST"])
def start_game():
    mode = request.json.get("mode", "hard")
    new_game(mode)
    return jsonify({"status": "ok"})


@app.route("/get_state", methods=["GET"])
def get_state():
    _, game = get_game()
    return jsonify(game)


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

    if pattern == "GGGGG" or len(game["guesses"]) >= MAX_GUESSES:
        game["game_over"] = True

        remaining_answers = [w for w in new_candidates if w in answers_set]

        if remaining_answers:
            final_word = random.choice(remaining_answers)
        else:
            final_word = random.choice(new_candidates)

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
    app.run(debug=False, use_reloader=False)