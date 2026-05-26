import json
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ── CLIENT ────────────────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-haiku-4-5-20251001"

# ── INVALID EXPECTED VALUES ───────────────────────────────────────────────────
INVALID_EXPECTED = {'not null', 'null', 'any', 'yes', 'no', 'none', 'unknown'}

def validate_question(q: dict) -> bool:
    """Check if expected_values contains meaningful data (not generic garbage)."""
    ev = [str(v).lower() for v in q.get('expected_values', [])]
    if any(v in INVALID_EXPECTED for v in ev):
        return False
    if not ev:
        return False
    return True

# ── HOW MANY CANDIDATES TO SHOW LLM BASED ON QUESTION NUMBER ─────────────────
def get_candidate_limit(question_number: int) -> int:
    if question_number <= 2:
        return 40
    elif question_number <= 4:
        return 25
    elif question_number <= 6:
        return 15
    else:
        return 10  # final stretch — show all remaining up to 10

# ── SLIM PROFILE FOR LLM CONTEXT ─────────────────────────────────────────────
def slim_profile(player: dict) -> dict:
    """Strip player profile to essential fields only — minimizes tokens."""
    return {
        'name':         player['player_name'],
        'nationality':  player.get('nationality'),
        'role':         player.get('derived_role'),
        'bat':          player.get('batting_style'),
        'bowl':         player.get('bowling_style'),
        'wk':           player.get('is_wicketkeeper'),
        'overseas':     player.get('is_overseas'),
        'active':       player.get('is_active'),
        'era':          player.get('debut_era'),
        'matches':      player.get('matches_bucket'),
        'runs':         player.get('runs_bucket'),
        'wickets':      player.get('wickets_bucket'),
        'title':        player.get('is_title_winner'),
        'superstar':    player.get('is_superstar'),
        'one_team':     player.get('one_franchise_player'),
        'teams':        player.get('teams_played_for', []),
        'potm':         player.get('potm_bucket'),
    }

# ── FORMAT HISTORY FOR PROMPT ─────────────────────────────────────────────────
def format_history(history: list) -> str:
    if not history:
        return "None yet."
    lines = []
    for i, h in enumerate(history, 1):
        lines.append(f"  Q{i}: {h['question']} → {h['answer'].upper()}")
    return '\n'.join(lines)

# ── BUCKET ATTRIBUTES TO EXCLUDE FROM LLM ──────────────────────────────────
BUCKET_ATTRS = {
    'matches_bucket', 'runs_bucket', 'wickets_bucket',
    'franchise_bucket', 'debut_era_granular', 'potm_bucket'
}

# ── FORMAT ATTRIBUTES FOR PROMPT ─────────────────────────────────────────────
def format_attributes(best_attributes: list, asked: set) -> str:
    lines = []
    rank = 1
    for attr, score in best_attributes:
        if attr not in asked and attr != 'teams_played_for' and attr not in BUCKET_ATTRS:
            lines.append(f"  {rank}. {attr} (info_gain={score:.2f})")
            rank += 1
        if rank > 8:  # only show top 8 unasked
            break
    return '\n'.join(lines) if lines else "  (all high-value attributes asked)"

# ── JOB 1: SELECT NEXT QUESTION ──────────────────────────────────────────────
def select_question(
    candidates: list,
    best_attributes: list,
    history: list,
    question_number: int,
    engine,
) -> dict:
    """
    Ask LLM to pick the next best question.
    Returns: {question, attribute, expected_values, reasoning}
    """
    asked_attrs = {h['attribute'] for h in history}

    # ── FIX 3: FORCE TOP ENTROPY ATTR FOR LARGE POOLS ────────────────────────
    # When pool > 20, LLM freelances and picks weak questions.
    # Force it to ask about the highest entropy attribute instead.
    if len(candidates) > 20 and best_attributes:
        top_attr, top_score = best_attributes[0]
        print(f"  [DEBUG] Fix3 triggered: forcing attr={top_attr}, score={top_score}")

        if top_attr not in asked_attrs and top_attr != 'teams_played_for':
            # Sample actual values so LLM knows what's possible
            sample_vals = list(set(
                str(engine._get_attribute(engine.player_map[p], top_attr))
                for p in list(engine.active_players)[:15]
            ))
            print(f"  [DEBUG] Fix3 sample vals: {sample_vals}")

            forced_response = client.messages.create(
                model=MODEL,
                system="You are an IPL Akinator. Generate ONE natural yes/no question for a cricket fan. JSON only.",
                messages=[{"role": "user", "content": f"""Generate a yes/no question about '{top_attr}' for an IPL player.

Actual values this attribute takes: {sample_vals}

Return JSON:
{{
  "question": "natural yes/no question a cricket fan would understand",
  "attribute": "{top_attr}",
  "expected_values": ["the value(s) that mean YES"],
  "reasoning": "forced: top entropy attr score={top_score:.2f}"
}}"""}],
                temperature=0.2,
                max_tokens=150,
            )

            raw   = forced_response.content[0].text.strip()
            clean = raw.split("```")[1].lstrip("json").strip() if "```" in raw else raw
            result = json.loads(clean)

            if isinstance(result['expected_values'], str):
                result['expected_values'] = [result['expected_values']]

            if validate_question(result):
                return result
            # if validation fails, fall through to normal LLM flow below

    # ── CHECK TEAM QUESTION FIRST ─────────────────────────────────────────
    top_attrs = [attr for attr, score in best_attributes if attr not in asked_attrs]
    if 'teams_played_for' in top_attrs[:3]:
        wk_asked = 'is_wicketkeeper' in asked_attrs
        overseas_asked = 'is_overseas' in asked_attrs
        if wk_asked and overseas_asked:  # ← only after priority attrs done
            team_q = engine.get_best_team_question(asked_attrs)
            if team_q:
                return team_q

    limit        = get_candidate_limit(question_number)
    top_players  = candidates[:limit]
    slim_players = [slim_profile(p) for p in top_players]

    asked_attrs  = {h['attribute'] for h in history}
    history_str  = format_history(history)
    attrs_str    = format_attributes(best_attributes, asked_attrs)

    # ── SYSTEM PROMPT ─────────────────────────────────────────────────────────
    system = (
        "You are an IPL Akinator. Identify IPL players (2008-2025) via yes/no questions.\n"
        "Maximize information gain. JSON only.\n\n"
        "BUCKET VALUES — use these exact strings in expected_values:\n"
        "matches_bucket: '10-29','30-59','60-99','100-149','150+'\n"
        "  e.g. '150+ matches?' → expected_values: ['150+']\n"
        "  e.g. '100+ matches?' → expected_values: ['100-149','150+']\n"
        "runs_bucket: '0-199','200-999','1000-2999','3000+'\n"
        "  e.g. '3000+ runs?' → expected_values: ['3000+']\n"
        "wickets_bucket: '0','1-24','25-74','75+'\n"
        "  e.g. '75+ wickets?' → expected_values: ['75+']\n"
        "franchise_bucket: '1 team','2-3 teams','4+ teams'\n"
        "  e.g. '4+ franchises?' → expected_values: ['4+ teams']\n"
        "debut_era: '2008-2012','2013-2017','2018+'\n"
        "derived_role: 'batter','bowler','all-rounder','wicketkeeper-batter','mixed'\n"
        "batting_style: 'right-hand bat','left-hand bat'\n"
        "For range questions, set ALL matching buckets e.g. 100+ matches → ['100-149','150+']"
    )

    # ── USER PROMPT ───────────────────────────────────────────────────────────
    user = f"""QUESTION {question_number}/8

REMAINING CANDIDATES ({len(candidates)} players, showing top {len(slim_players)}):
{json.dumps(slim_players, separators=(',', ':'))}

QUESTIONS ASKED:
{history_str}

BEST ATTRIBUTES TO ASK (ranked by info gain, pick from top):
{attrs_str}

TASK: Pick ONE yes/no question from the top attributes above.
- Prefer attributes with highest info_gain
- Do NOT repeat asked attributes
- Phrase naturally for a cricket fan
- If ≤5 candidates remain, ask most distinguishing question between them

Return JSON:
{{
  "question": "natural yes/no question for the user",
  "attribute": "exact attribute name from list",
  "expected_values": ["value that means YES"],
  "reasoning": "brief reason (1 line)"
}}"""

    # ── RETRY LOOP FOR VALID QUESTIONS ───────────────────────────────────────
    max_retries = 3
    for attempt in range(max_retries):
        response = client.messages.create(
            model=MODEL,
            system=system,
            messages=[
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=200,
        )

        raw = response.content[0].text

        # Strip markdown fences if present
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()

        result = json.loads(clean)

        # Validate required fields
        required = ['question', 'attribute', 'expected_values']
        for field in required:
            if field not in result:
                raise ValueError(f"LLM response missing field: {field}")

        # Ensure expected_values is a list
        if isinstance(result['expected_values'], str):
            result['expected_values'] = [result['expected_values']]

        # Validate expected_values are meaningful
        if validate_question(result):
            return result

        # If invalid, re-prompt and retry
        if attempt < max_retries - 1:
            user += "\n\nPREVIOUS ATTEMPT REJECTED: expected_values must be specific player attributes, NOT generic values like 'yes', 'no', 'any', 'null'. Try again."

    # If all retries fail, raise error
    raise ValueError(f"LLM failed to generate valid question after {max_retries} attempts. Last response: {result}")

# ── JOB 2: MAKE FINAL GUESS ───────────────────────────────────────────────────
def make_final_guess(
    top_candidates: list,
    history: list,
) -> dict:
    """
    Ask LLM to make final guess based on top candidates + history.
    Returns: {guess, confidence, reasoning, display_message}
    """
    history_str = format_history(history)

    # Extract top candidate
    top_name = top_candidates[0]['player_name']
    top_prob = top_candidates[0]['probability']

    # Format top candidates with probabilities
    candidates_str = '\n'.join([
        f"  {i+1}. {c['player_name']} ({c['probability']*100:.1f}%) — "
        f"{c['profile'].get('nationality')}, {c['profile'].get('derived_role')}, "
        f"era:{c['profile'].get('debut_era')}, matches:{c['profile'].get('matches_bucket')}"
        for i, c in enumerate(top_candidates[:5])
    ])

    system = (
        "You are the IPL Akinator. Make a confident, fun final guess.\n"
        "Cross-check your guess against ALL yes/no answers before deciding.\n"
        "JSON only. Format:\n"
        '{"guess":"player name","confidence":0.0-1.0,'
        '"reasoning":"2 sentences max","display_message":"fun dramatic reveal"}'
    )

    user = f"""FINAL GUESS

Q&A HISTORY:
{history_str}

TOP CANDIDATES (RANKED BY PROBABILITY — #1 is most likely):
{candidates_str}

YOUR GUESS MUST BE: {top_name} ({top_prob*100:.0f}% probability)
Only override if their profile CLEARLY contradicts a YES answer.
Verify: does {top_name} match all YES answers above?

Return JSON:
{{
  "guess": "{top_name}",
  "confidence": {top_prob},
  "reasoning": "2-3 line explanation of why this player fits all clues",
  "display_message": "fun akinator-style message e.g. 'I think you are thinking of... MS Dhoni!'"
}}"""

    response = client.messages.create(
        model=MODEL,
        system=system,
        messages=[
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=250,
    )

    raw = response.content[0].text

    # Strip markdown fences if present
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
        clean = clean.strip()

    result = json.loads(clean)
    return result

# ── QUICK TEST ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    sys.path.append('.')
    from backend.bayes_engine import BayesEngine

    engine = BayesEngine('ipl_player_profiles.json')

    print("Testing question selection...")
    candidates    = engine.get_remaining_candidates()
    best_attrs    = engine.get_best_attributes()
    history       = []

    q1 = select_question(candidates, best_attrs, history, question_number=1, engine=engine)
    print(f"\nQ1: {q1['question']}")
    print(f"    attribute: {q1['attribute']}")
    print(f"    expected:  {q1['expected_values']}")
    print(f"    reasoning: {q1.get('reasoning', '')}")

    # Simulate answer: yes to Q1
    engine.update(q1['attribute'], q1['expected_values'], 'yes')
    history.append({
        'question':        q1['question'],
        'attribute':       q1['attribute'],
        'expected_values': q1['expected_values'],
        'answer':          'yes',
    })

    print(f"\nAfter Q1: {engine.get_remaining_count()} candidates remaining")
    print(f"Confidence: {engine.get_confidence()}")

    # Q2
    candidates = engine.get_remaining_candidates()
    best_attrs = engine.get_best_attributes()
    q2 = select_question(candidates, best_attrs, history, question_number=2, engine=engine)
    print(f"\nQ2: {q2['question']}")
    print(f"    attribute: {q2['attribute']}")