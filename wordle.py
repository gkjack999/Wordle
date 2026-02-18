from collections import defaultdict

WORD_LENGTH = 5
MAX_GUESSES = 6


def load_word_list(filename):
    with open(filename) as f:
        return [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]


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

    best_pattern = None
    best_group = None

    for pattern, group in buckets.items():
        if best_group is None or len(group) > len(best_group):
            best_pattern = pattern
            best_group = group

    return best_pattern, best_group


def print_pattern(guess, pattern):
    for i in range(WORD_LENGTH):
        if pattern[i] == "G":
            print(f"\033[92m{guess[i].upper()}\033[0m", end=" ")
        elif pattern[i] == "Y":
            print(f"\033[93m{guess[i].upper()}\033[0m", end=" ")
        else:
            print(f"\033[90m{guess[i].upper()}\033[0m", end=" ")
    print()


def choose_final_word(candidates, answers):
    """
    At the end of the game:
    - Prefer a word that exists in the official answers list.
    - If none remain, fall back to any remaining candidate.
    """
    candidates_set = set(candidates)
    answers_set = set(answers)

    valid_answers_remaining = candidates_set & answers_set

    if valid_answers_remaining:
        return sorted(valid_answers_remaining)[0]
    elif candidates:
        return sorted(candidates)[0]
    else:
        # Extremely rare fallback
        return sorted(answers)[0]


def main():
    answers = load_word_list("wordle-answers.txt")
    guesses_extra = load_word_list("wordle-guesses.txt")

    ALL_GUESSES = set(answers) | set(guesses_extra)
    candidates = answers.copy()

    print("Wordle")
    print()

    for turn in range(1, MAX_GUESSES + 1):
        guess = input(f"Guess {turn}/6: ").lower().strip()

        if guess not in ALL_GUESSES:
            print("Not in word list.")
            continue

        pattern, new_candidates = choose_max_remaining_pattern(guess, candidates)
        candidates = new_candidates

        print_pattern(guess, pattern)

        if pattern == "GGGGG":
            final_word = choose_final_word(candidates, answers)
            print("\nCorrect.")
            print(f"The word was {final_word.upper()}.")
            return

    # Player failed after 6 guesses
    final_word = choose_final_word(candidates, answers)

    print("\nUnlucky.")
    print(f"The word was {final_word.upper()}.")


if __name__ == "__main__":
    main()
