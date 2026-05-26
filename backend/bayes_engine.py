import json
import math
from typing import Optional

# ── ANSWER WEIGHTS ────────────────────────────────────────────────────────────
# How much each answer type shifts probability
ANSWER_WEIGHTS = {
    'yes':        1.0,   # full update
    'no':         1.0,   # full update (inverted)
    'maybe':      0.5,   # soft update
    'dont_know':  0.0,   # skip — no information
}

# How much a non-matching player is penalized
MISMATCH_PENALTY = 0.05   # non-matching player → multiplied by 0.05
MATCH_BOOST      = 1.0    # matching player → unchanged (relative boost via penalty)

# ── LLM-VISIBLE ATTRIBUTES ────────────────────────────────────────────────────
# Only these attributes are shown to LLM for question selection
LLM_ATTRIBUTES = [
    'is_wicketkeeper',
    'is_overseas',
    'is_likely_captain',   # ← ADD
    'is_active',
    'is_title_winner',
    'is_superstar',
    'one_franchise_player',
    'elite_batter',
    'elite_bowler',
    'nationality',
    'derived_role',
    'batting_style',
    'debut_era',
    'teams_played_for',
    'matches_bucket',
    'runs_bucket',
    'wickets_bucket',
    'franchise_bucket',
    'potm_bucket',         # ← ADD
]

# ── EXCLUDED BUCKETS ──────────────────────────────────────────────────────────
# Attributes to exclude from format_attributes() output
BUCKET_ATTRS = {
    'debut_era_granular',   # Too granular for most users
}


class BayesEngine:
    def __init__(self, players_path: str):
        """
        Load player profiles and initialize uniform priors.
        players_path: path to ipl_player_profiles.json
        """
        with open(players_path, 'r') as f:
            self.all_players = json.load(f)

        # Uniform prior — every player equally likely at start
        n = len(self.all_players)
        self.probabilities = {
            p['player_name']: 1.0 / n
            for p in self.all_players
        }

        # Track which players are still active (not eliminated)
        self.active_players = {p['player_name'] for p in self.all_players}

        # Player lookup by name
        self.player_map = {p['player_name']: p for p in self.all_players}

        # Question history: list of {question, attribute, answer, expected_values}
        self.history = []

    # ── CORE: UPDATE PROBABILITIES ────────────────────────────────────────────
    def update(self, attribute: str, expected_values, answer: str):
        """
        Update probabilities based on user's answer.

        attribute:       field in player profile e.g. 'nationality'
        expected_values: value(s) that correspond to 'yes'
                         can be a single value or list e.g. 'India' or ['India', 'Pakistan']
        answer:          'yes' | 'no' | 'maybe' | 'dont_know'
        """
        weight = ANSWER_WEIGHTS.get(answer.lower().strip(), 0.0)
        
        # DEBUG
        before = len(self.active_players)
        sample = list(self.active_players)[:3]
        sample_vals = [self._get_attribute(self.player_map[p], attribute) for p in sample]
        print(f"  [DEBUG] attribute={attribute}, expected={expected_values}, answer={answer}")
        print(f"  [DEBUG] sample player values: {list(zip(sample, sample_vals))}")
        print(f"  [DEBUG] weight={weight}")

        answer = answer.lower().strip()

        if weight == 0.0:
            # Don't Know — no update
            self.history.append({
                'attribute': attribute,
                'expected_values': expected_values,
                'answer': answer,
            })
            return

        if isinstance(expected_values, str):
            expected_values = [expected_values]
        expected_values = [
            ('true' if v else 'false') if isinstance(v, bool) else str(v).lower() 
            for v in expected_values
        ]

        # ── DYNAMIC PENALTY based on pool size ───────────────────────────────
        n = len(self.active_players)
        if n <= 3:
            dynamic_penalty = 0.001   # near-elimination for tiny pools
        elif n <= 5:
            dynamic_penalty = 0.01
        else:
            dynamic_penalty = MISMATCH_PENALTY   # 0.05 default

        for player_name in list(self.active_players):
            player = self.player_map[player_name]
            player_value = self._get_attribute(player, attribute)

            # Does this player match the expected value?
            matches = self._check_match(player_value, expected_values)

            if answer in ('yes', 'maybe'):
                if not matches:
                    # Player doesn't match — penalize
                    penalty = dynamic_penalty if answer == 'yes' else (1 - weight * (1 - dynamic_penalty))
                    self.probabilities[player_name] *= penalty
            elif answer == 'no':
                if matches:
                    # Player matches but answer was no — penalize
                    penalty = dynamic_penalty if answer == 'no' else (1 - weight * (1 - dynamic_penalty))
                    self.probabilities[player_name] *= penalty

        # Count how many players got penalized
        penalized = sum(
            1 for name in self.active_players
            if self.probabilities[name] < (1.0 / len(self.active_players))
        )
        print(f"  [DEBUG] penalized: {penalized} players")

        top_prob = max(self.probabilities[n] for n in self.active_players)
        min_prob = min(self.probabilities[n] for n in self.active_players)
        print(f"  [DEBUG] top_prob={top_prob:.8f}, min_prob={min_prob:.8f}")

        # Renormalize
        self._renormalize()

        # Eliminate bottom players
        self._eliminate_low_probability()
        print(f"  [DEBUG] after elimination: {len(self.active_players)} players")

        # Log history
        self.history.append({
            'attribute':       attribute,
            'expected_values': expected_values,
            'answer':          answer,
        })

    # ── GET RANKED CANDIDATES ─────────────────────────────────────────────────
    def get_top_candidates(self, n: int = 10):
        """Return top N candidates sorted by probability."""
        ranked = sorted(
            [(name, self.probabilities[name]) for name in self.active_players],
            key=lambda x: x[1],
            reverse=True
        )[:n]

        return [
            {
                'player_name': name,
                'probability': round(prob, 6),
                'profile':     self.player_map[name],
            }
            for name, prob in ranked
        ]

    def get_remaining_candidates(self):
        """Return full profiles of all active candidates, sorted by probability."""
        ranked = sorted(
            self.active_players,
            key=lambda name: self.probabilities[name],
            reverse=True
        )
        return [self.player_map[name] for name in ranked]

    def get_confidence(self):
        """
        Return confidence score of top candidate (0-1).
        Confidence = probability of top candidate.
        """
        if not self.active_players:
            return 0.0
        top_prob = max(self.probabilities[name] for name in self.active_players)
        return round(top_prob, 4)

    def get_top_player(self):
        """Return the current most likely player."""
        if not self.active_players:
            return None
        top_name = max(self.active_players, key=lambda name: self.probabilities[name])
        return {
            'player_name': top_name,
            'probability': round(self.probabilities[top_name], 4),
            'profile':     self.player_map[top_name],
        }

    def should_guess(self, threshold: float = 0.80):
        """Return True if top candidate exceeds confidence threshold."""
        # Also guess if only 1-2 players remain regardless of confidence
        if len(self.active_players) <= 2:
            return True
        return self.get_confidence() >= threshold

    def get_remaining_count(self):
        return len(self.active_players)

    def get_entropy(self):
        """
        Current entropy of the probability distribution.
        Lower entropy = more certain = closer to a guess.
        """
        total = sum(self.probabilities[n] for n in self.active_players)
        if total == 0:
            return 0.0
        entropy = 0.0
        for name in self.active_players:
            p = self.probabilities[name] / total
            if p > 0:
                entropy -= p * math.log2(p)
        return round(entropy, 4)

    # ── ENTROPY-BASED QUESTION SCORING ────────────────────────────────────────
    def score_attribute(self, attribute: str) -> float:
        """
        Score information gain of an attribute across active players.
        Handles multi-value attributes (lists) correctly.
        """
        candidates = [self.player_map[n] for n in self.active_players]
        if not candidates:
            return 0.0

        total = len(candidates)
        value_counts = {}

        for player in candidates:
            val = self._get_attribute(player, attribute)

            if isinstance(val, list):
                # Multi-value: count each unique value separately
                # e.g. teams_played_for = ['CSK', 'MI'] → increment both
                seen = set()  # avoid double-counting same value in one player
                for v in val:
                    v = str(v).lower()
                    if v not in seen:
                        value_counts[v] = value_counts.get(v, 0) + 1
                        seen.add(v)
            else:
                v = str(val).lower()
                value_counts[v] = value_counts.get(v, 0) + 1

        if not value_counts:
            return 0.0

        # Entropy over the value distribution
        entropy = 0.0
        for count in value_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        return round(entropy, 4)

    def get_best_attributes(self):
        """
        Rank all attributes by their information gain with strategic priority boost.
        Returns sorted list of (attribute, final_score).
        """
        # ── FORCE-GUESS WHEN FEW PLAYERS REMAIN ───────────────────────────────
        # When ≤2 players left, no question can split them meaningfully
        # Return empty list to signal game.py to guess instead
        if len(self.active_players) <= 2:
            return []
        
        # Start with LLM-visible attributes
        attributes = list(LLM_ATTRIBUTES)

        # exclude teams_played_for — handled programmatically
        attributes = [a for a in attributes if a != 'teams_played_for']

        # Filter out already asked attributes
        asked = {h['attribute'] for h in self.history}
        attributes = [a for a in attributes if a not in asked]

        PRIORITY_BOOST = {
    # Core identity — ask these first, fan friendly
    'is_wicketkeeper':      5.0,
    'is_overseas':          4.0,
    'is_likely_captain':    3.5,
    'derived_role':         2.5,   # ← up, "is this player a bowler?" is natural Q2
    'batting_style':        2.0,   # ← up, natural early question
    'is_active':            2.0,   # ← up
    'is_superstar':         1.8,   # ← up

    # Secondary identity
    'is_title_winner':      1.5,
    'one_franchise_player': 1.5,
    'elite_batter':         1.3,
    'elite_bowler':         1.3,
    'debut_era':            1.2,
    'nationality':          1.1,

    # Stats buckets — useful but not fan friendly, ask late
    'matches_bucket':       0.8,   # ← down from 3.0
    'runs_bucket':          0.8,   # ← down from 2.5
    'wickets_bucket':       0.8,   # ← down from 2.0
    'franchise_bucket':     0.8,   # ← down from 2.0
    'potm_bucket':          0.6,   # ← down, least intuitive
    'teams_played_for':     1.5,
}
        scored = []
        for attr in attributes:
            entropy = self.score_attribute(attr)
            
            # ── KEY FIX: skip zero-entropy attributes entirely ──────────────
            # Zero entropy = all remaining players have same value = useless question
            if entropy == 0.0:
                continue
            
            boost = PRIORITY_BOOST.get(attr, 1.0)
            # Multiply only — no floor. Tiebreaker via tiny boost offset.
            final_score = (entropy * boost) + (boost * 0.001)
            scored.append((attr, round(final_score, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def get_best_team_question(self, asked_attributes: set) -> dict | None:
        if 'teams_played_for' in asked_attributes:
            return None

        ALL_TEAMS = [
            "Chennai Super Kings", "Mumbai Indians",
            "Royal Challengers Bangalore", "Kolkata Knight Riders",
            "Sunrisers Hyderabad", "Rajasthan Royals",
            "Delhi Capitals", "Punjab Kings",
            "Gujarat Titans", "Lucknow Super Giants",
            "Deccan Chargers", "Rising Pune Supergiants",
            "Gujarat Lions",
        ]

        total = len(self.active_players)
        if total == 0:
            return None

        best_team  = None
        best_score = -1

        for team in ALL_TEAMS:
            count = sum(
                1 for name in self.active_players
                if team in self.player_map[name].get('teams_played_for', [])
            )
            if count == 0 or count == total:
                continue
            p = count / total
            split_score = 1 - abs(p - 0.5) * 2
            if split_score > best_score:
                best_score = split_score
                best_team  = team

        if not best_team:
            return None

        return {
            'question':        f"Has your player ever played for {best_team}?",
            'attribute':       'teams_played_for',
            'expected_values': [best_team],
            'reasoning':       f"Best team split ({best_score:.2f} score)",
            'source':          'programmatic',
        }
    
    def eliminate_player(self, player_name: str):
        """Remove wrongly guessed player and renormalize."""
        self.active_players.discard(player_name)
        self.probabilities.pop(player_name, None)
        self._renormalize()

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _get_attribute(self, player: dict, attribute: str):
        """Safely get attribute from player profile."""
        val = player.get(attribute)
        if val is None:
            return 'unknown'
        if isinstance(val, bool):
            return str(val).lower()  # True → 'true', False → 'false'
        if isinstance(val, list):
            return [str(v).lower() for v in val]
        return str(val).lower()

    def _check_match(self, player_value, expected_values: list) -> bool:
        if isinstance(player_value, list):
            player_list = [str(v).lower() for v in player_value]
            return any(ev.lower() in player_list for ev in expected_values)
        
        # Numeric threshold matching e.g. "potm_count > 5"
        for ev in expected_values:
            if isinstance(ev, str) and ev.startswith('>'):
                try:
                    threshold = float(ev[1:])
                    return float(player_value) > threshold
                except ValueError:
                    pass
            elif isinstance(ev, str) and ev.startswith('<'):
                try:
                    threshold = float(ev[1:])
                    return float(player_value) < threshold
                except ValueError:
                    pass
        
        return str(player_value).lower() in expected_values
    def _renormalize(self):
        """Renormalize probabilities of active players to sum to 1."""
        total = sum(self.probabilities[n] for n in self.active_players)
        if total > 0:
            for name in self.active_players:
                self.probabilities[name] /= total

    def _eliminate_low_probability(self):
        if not self.active_players:
            return
        top_prob = max(self.probabilities[n] for n in self.active_players)
        n = len(self.active_players)
        
        if n > 200:
            cutoff = top_prob * 0.15
        elif n > 50:
            cutoff = top_prob * 0.10
        elif n > 15:
            cutoff = top_prob * 0.08
        elif n > 5:
            cutoff = top_prob * 0.15   # tighter for 6-15 players
        elif n > 2:
            cutoff = top_prob * 0.30   # aggressive for 3-5 players
        else:
            cutoff = top_prob * 0.50   # near-equal split of 2 → eliminate loser fast
        
        self.active_players = {
            p for p in self.active_players
            if self.probabilities[p] >= cutoff
        }

    def get_state_summary(self):
        """Return a summary of current game state for LLM context."""
        top = self.get_top_candidates(5)
        return {
            'remaining_count':  self.get_remaining_count(),
            'confidence':       self.get_confidence(),
            'entropy':          self.get_entropy(),
            'top_candidates':   top,
            'questions_asked':  len(self.history),
            'best_attributes':  self.get_best_attributes()[:5],
            'history':          self.history,
        }


# ── QUICK TEST ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    engine = BayesEngine('ipl_player_profiles.json')

    print(f"Loaded {len(engine.all_players)} players")
    print(f"Initial entropy: {engine.get_entropy()}")
    print(f"Initial confidence: {engine.get_confidence()}")
    print(f"Best attributes to ask: {engine.get_best_attributes()[:5]}")

    # Simulate: thinking of MS Dhoni
    print("\n── Simulating: MS Dhoni ──")

    engine.update('nationality', 'India', 'yes')
    print(f"After 'Indian?=yes': {engine.get_remaining_count()} candidates, entropy={engine.get_entropy()}")

    engine.update('batting_style', 'right-hand bat', 'yes')
    print(f"After 'RHB?=yes': {engine.get_remaining_count()} candidates, entropy={engine.get_entropy()}")

    engine.update('debut_era', '2008-2012', 'yes')
    print(f"After 'debut 2008-12?=yes': {engine.get_remaining_count()} candidates, entropy={engine.get_entropy()}")

    engine.update('matches_bucket', '150+', 'yes')
    print(f"After '150+ matches?=yes': {engine.get_remaining_count()} candidates, entropy={engine.get_entropy()}")

    engine.update('is_title_winner', 'true', 'yes')
    print(f"After 'title winner?=yes': {engine.get_remaining_count()} candidates, entropy={engine.get_entropy()}")

    print(f"\nConfidence: {engine.get_confidence()}")
    print(f"Should guess: {engine.should_guess()}")
    print(f"\nTop 5 candidates:")
    for c in engine.get_top_candidates(5):
        print(f"  {c['player_name']}: {c['probability']:.4f}")