import uuid
import os
from backend.bayes_engine import BayesEngine
from backend.llm_engine import select_question, make_final_guess


# ── CONSTANTS ─────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
PLAYERS_PATH   = os.path.join(BASE_DIR, "ipl_player_profiles.json")
MAX_QUESTIONS      = 8
CONFIDENCE_THRESHOLD = 0.80

# ── IN-MEMORY SESSION STORE ───────────────────────────────────────────────────
# session_id → {engine, history, question_count, state, current_question}
sessions = {}


# ── SESSION MANAGEMENT ────────────────────────────────────────────────────────
def new_game() -> dict:
    """
    Start a new game session.
    Returns session_id + first question.
    """
    session_id = str(uuid.uuid4())

    engine = BayesEngine(PLAYERS_PATH)
    print("Attribute ranking:", engine.get_best_attributes()[:8])

    # Get first question immediately
    candidates = engine.get_remaining_candidates()
    best_attrs = engine.get_best_attributes()
    question = select_question(
    candidates=candidates,
    best_attributes=best_attrs,
    history=[],
    question_number=1,
    engine=engine,           # ← add
)

    sessions[session_id] = {
        'engine':           engine,
        'history':          [],
        'question_count':   1,
        'state':            'playing',  # playing | guessing | done
        'current_question': question,
        'last_guess':       None,   
    }

    top_candidates = engine.get_top_candidates(5)

    return {
        'session_id':       session_id,
        'question_number':  1,
        'question':         question['question'],
        'attribute':        question['attribute'],
        'remaining_count':  engine.get_remaining_count(),
        'confidence':       engine.get_confidence(),
        'state':            'playing',
        'top_candidates':  [                        # ← add this
            {
                'player_name': c['player_name'],
                'probability': c['probability'],
                'image_url':   c['profile'].get('image_url'),
            }
            for c in top_candidates[:5]
        ],
    }


def process_answer(session_id: str, answer: str) -> dict:
    """
    Process user's answer and return next question or final guess.

    answer: 'yes' | 'no' | 'maybe' | 'dont_know'
    """
    if session_id not in sessions:
        raise ValueError(f"Session {session_id} not found. Start a new game.")

    session = sessions[session_id]

    if session['state'] == 'done':
        raise ValueError("Game is already over. Start a new game.")

    engine           = session['engine']
    history          = session['history']
    question_count   = session['question_count']
    current_question = session['current_question']

    # ── 1. UPDATE BAYES WITH ANSWER ───────────────────────────────────────────
    engine.update(
        attribute=current_question['attribute'],
        expected_values=current_question['expected_values'],
        answer=answer,
    )

    # ── 2. LOG TO HISTORY ─────────────────────────────────────────────────────
    history.append({
        'question':        current_question['question'],
        'attribute':       current_question['attribute'],
        'expected_values': current_question['expected_values'],
        'answer':          answer,
    })

    remaining_count = engine.get_remaining_count()
    confidence      = engine.get_confidence()
    
    # Check available attributes early (returns [] if ≤2 players)
    best_attrs = engine.get_best_attributes()

    # ── FORCE GUESS if no attribute can split remaining players ───────────────
    if remaining_count <= 3:
        if not best_attrs:  # all attributes have zero entropy — no split possible
            top_candidates = engine.get_top_candidates(5)
            guess = make_final_guess(top_candidates, history)
            session['state'] = 'guessing'
            session['last_guess'] = guess['guess']
            return {
                'state': 'guessing',
                'guess': guess['guess'],
                'confidence': top_candidates[0]['probability'],
                'reasoning': guess['reasoning'],
                'display_message': guess['display_message'],
                'questions_asked': question_count,
                'top_candidates': [
                    {
                        'player_name': c['player_name'],
                        'probability': c['probability'],
                        'image_url': c['profile'].get('image_url'),
                    }
                    for c in top_candidates[:5]
                ],
            }

    # ── 3A. IMMEDIATE GUESS IF ONLY 1 PLAYER LEFT ────────────────────────────
    if remaining_count == 1:
        top_candidates = engine.get_top_candidates(1)
        guess = make_final_guess(top_candidates, history)
        session['state'] = 'guessing'
        session['last_guess'] = guess['guess']
        return {
            'state': 'guessing',
            'guess': guess['guess'],
            'confidence': 1.0,
            'reasoning': guess['reasoning'],
            'display_message': guess['display_message'],
            'questions_asked': question_count,
            'top_candidates': [{
                'player_name': top_candidates[0]['player_name'],
                'probability': 1.0,
                'image_url': top_candidates[0]['profile'].get('image_url'),
            }],
        }

    # ── 3B. DECIDE: GUESS OR CONTINUE ─────────────────────────────────────────
    should_guess = (
        confidence >= CONFIDENCE_THRESHOLD or
        question_count >= MAX_QUESTIONS    or
        remaining_count <= 2               or
        len(best_attrs) == 0               # Force guess when no useful attributes
    )

    if should_guess:
        # ── FINAL GUESS ───────────────────────────────────────────────────────
        top_candidates = engine.get_top_candidates(5)
        guess          = make_final_guess(
            top_candidates=top_candidates,
            history=history,
        )

        session['state'] = 'done'
        session['last_guess'] = guess['guess']   # ← add this

        return {
            'state':           'done',
            'guess':           guess['guess'],
            'confidence':      top_candidates[0]['probability'],
            'reasoning':       guess['reasoning'],
            'display_message': guess['display_message'],
            'top_candidates':  [
                {
                    'player_name': c['player_name'],
                    'probability': c['probability'],
                    'image_url':   c['profile'].get('image_url'),
                }
                for c in top_candidates[:5]
            ],
            'questions_asked': question_count,
            'history':         history,
        }

    else:
        # ── NEXT QUESTION ─────────────────────────────────────────────────────
        next_question_number = question_count + 1
        candidates           = engine.get_remaining_candidates()
        # best_attrs already computed above in should_guess check
        
        # ── TRY TEAM QUESTION FOR SMALL POOLS ─────────────────────────────────
        # When ≤5 players remain, team question is often best splitter
        if remaining_count <= 5:
            asked_attrs = {h['attribute'] for h in history}
            team_q = engine.get_best_team_question(asked_attrs)
            if team_q:
                next_question = team_q
            else:
                next_question = select_question(
                    candidates=candidates,
                    best_attributes=best_attrs,
                    history=history,
                    question_number=next_question_number,
                    engine=engine
                )
        else:
            next_question = select_question(
                candidates=candidates,
                best_attributes=best_attrs,
                history=history,
                question_number=next_question_number,
                engine=engine
            )

        # Update session
        session['question_count']   = next_question_number
        session['current_question'] = next_question

        top_candidates = engine.get_top_candidates(5) 
        
        return {
            'state':            'playing',
            'question_number':  next_question_number,
            'question':         next_question['question'],
            'attribute':        next_question['attribute'],
            'remaining_count':  remaining_count,
            'confidence':       confidence,
            'questions_asked':  question_count,
            'top_candidates':  [                        # ← add this block
                {
                    'player_name': c['player_name'],
                    'probability': c['probability'],
                    'image_url':   c['profile'].get('image_url'),
                }
                for c in top_candidates[:5]
            ],
        }

def process_feedback(session_id: str, was_correct: bool, correct_player: str = None) -> dict:
    if session_id not in sessions:
        raise ValueError(f"Session {session_id} not found.")
    
    session = sessions[session_id]
    engine  = session['engine']
    
    if was_correct:
        session['state'] = 'done'
        return {'state': 'done', 'message': 'Great! Glad I got it right!'}
    
    # Wrong guess — eliminate guessed player
    wrong_guess = session['last_guess']
    engine.eliminate_player(wrong_guess)
    
    # Boost correct player if provided
    if correct_player and correct_player in engine.player_map:
        if correct_player in engine.active_players:
            engine.probabilities[correct_player] *= 10.0
            engine._renormalize()
    
    remaining = engine.get_remaining_count()
    
    # ── NO PLAYERS LEFT → sorry screen ───────────────────────────────────────
    if remaining == 0:
        session['state'] = 'done'
        return {
            'state':   'done',
            'message': 'I give up! I could not guess your player.'
        }
    
    best_attrs = engine.get_best_attributes()
    
    # ── NO SPLITTABLE ATTRIBUTES LEFT → sorry screen ─────────────────────────
    if not best_attrs:
        session['state'] = 'done'
        return {
            'state':   'done',
            'message': 'I give up! I could not guess your player.'
        }

    # ── RESET QUESTION COUNTER for new round ─────────────────────────────────
    # Save old history for LLM context (avoid repeating questions)
    old_history = session['history'].copy()
    session['history'] = []
    session['question_count'] = 0

    # ── ASK NEXT QUESTION ────────────────────────────────────────────────────
    session['state'] = 'playing'
    candidates = engine.get_remaining_candidates()
    best_attrs = engine.get_best_attributes()  # now sees all attrs as fresh
    next_q = select_question(
        candidates=candidates,
        best_attributes=best_attrs,
        history=old_history,           # ← pass old history so LLM avoids repeats
        question_number=1,
        engine=engine,
    )
    
    session['question_count']  = 1
    session['current_question'] = next_q
    top_candidates = engine.get_top_candidates(5)

    return {
        'state':           'playing',
        'question_number': 1,
        'question':        next_q['question'],
        'remaining_count': engine.get_remaining_count(),
        'message':         'Oops! Let me think again...',
        'top_candidates':  [
            {
                'player_name': c['player_name'],
                'probability': c['probability'],
                'image_url':   c['profile'].get('image_url'),
            }
            for c in top_candidates[:5]
        ],
    }

def get_session_state(session_id: str) -> dict:
    """Return current state of a session — useful for debugging."""
    if session_id not in sessions:
        raise ValueError(f"Session {session_id} not found.")

    session = sessions[session_id]
    engine  = session['engine']

    return {
        'session_id':      session_id,
        'state':           session['state'],
        'question_count':  session['question_count'],
        'remaining_count': engine.get_remaining_count(),
        'confidence':      engine.get_confidence(),
        'entropy':         engine.get_entropy(),
        'top_candidates':  engine.get_top_candidates(5),
        'history':         session['history'],
    }


def cleanup_session(session_id: str):
    """Remove session from memory."""
    sessions.pop(session_id, None)


def pretty_print_candidates(top_candidates: list):
    print("\n  📊 Top candidates:")
    for i, c in enumerate(top_candidates, 1):
        prob = c['probability']
        bar  = '█' * int(prob * 30) + '░' * (30 - int(prob * 30))
        print(f"  {i}. {c['player_name']:<25} {bar} {prob*100:5.1f}%")
    print()



#____________TEST_______________________

if __name__ == '__main__':
    print("Starting new game...")
    game = new_game()
    print(f"Q1: {game['question']}")
    print(f"Remaining: {game['remaining_count']} players")
    # pretty_print_candidates(game['top_candidates'])  ← removed

    sid = game['session_id']

    while True:
        state = sessions[sid]['state']

        if state == 'playing':
            answer = input("Your answer (yes/no/maybe/dont_know): ").strip().lower()
            result = process_answer(sid, answer)

            if result['state'] in ('guessing', 'done'):
                # ── HANDLE GUESS ──────────────────────────────────────────
                print(f"\n🔮 {result['display_message']}")
                print(f"Confidence: {result['confidence']:.2%}")
                print(f"Reasoning: {result['reasoning']}")
                pretty_print_candidates(result['top_candidates'])

                feedback = input("\nWas I correct? (yes/no): ").strip().lower()
                if feedback == 'yes':
                    process_feedback(sid, was_correct=True)
                    print("🎉 Great! Thanks for playing!")
                    break
                else:
                    result = process_feedback(sid, was_correct=False)
                    if result['state'] == 'done':
                        print("I give up! I couldn't guess your player.")
                        break
                    print(f"\nLet me try again...")
                    print(f"Q{result['question_number']}: {result['question']}")
                    print(f"Remaining: {result['remaining_count']} players")

            elif result['state'] == 'playing':
                print(f"Q{result['question_number']}: {result['question']}")
                print(f"Remaining: {result['remaining_count']} players")
                print(f"Confidence: {result['confidence']:.2%}")
                pretty_print_candidates(result['top_candidates'])

        elif state in ('guessing', 'done'):
            # Safety net — session stuck in guess state, force feedback prompt
            session  = sessions[sid]
            engine   = session['engine']
            top      = engine.get_top_candidates(5)
            guess    = session.get('last_guess', top[0]['player_name'])

            print(f"\n🔮 My best guess is: {guess}")
            pretty_print_candidates(top)

            feedback = input("\nWas I correct? (yes/no): ").strip().lower()
            if feedback == 'yes':
                process_feedback(sid, was_correct=True)
                print("🎉 Great! Thanks for playing!")
                break