from collections import defaultdict
import random

WORD_LENGTH = 5

SEQUENCE = ["adieu", "plate", "clank", "maple", "bacon", "waken"]


def load_word_list(filename):
    with open(filename) as f:
        return [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]


answers = load_word_list("wordle-answers.txt")
guesses_extra = load_word_list("wordle-guesses.txt")

ALL_GUESSES = list(set(answers) | set(guesses_extra))


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


def choose_max_remaining_pattern(guess, candidates):
    buckets = defaultdict(list)

    for answer in candidates:
        pattern = score_pattern(guess, answer)
        buckets[pattern].append(answer)

    max_size = max(len(group) for group in buckets.values())

    # Deterministic max bucket (same as app)
    for pattern, group in buckets.items():
        if len(group) == max_size:
            return pattern, group


def run_sequence():
    candidates = ALL_GUESSES.copy()

    print("Initial universe size:", len(candidates))
    print()

    patterns = []

    for guess in SEQUENCE:
        pattern, candidates = choose_max_remaining_pattern(guess, candidates)
        patterns.append(pattern)
        print(f"Guess: {guess.upper()}  Pattern: {pattern}  Remaining: {len(candidates)}")

    print("\nFinal candidate count:", len(candidates))

    # Split remaining into answers vs guesses
    answers_set = set(answers)
    remaining_answers = sorted([w for w in candidates if w in answers_set])

    print("\nRemaining OFFICIAL answers:", len(remaining_answers))
    for word in remaining_answers:
        print(word)

    if remaining_answers:
        chosen = random.choice(remaining_answers)
        print("\nRandom chosen answer (from answers only):", chosen.upper())
    else:
        print("\nNo official answers remain.")


if __name__ == "__main__":
    run_sequence()
