"""
TF-IDF token importance scoring and pruning.

Replaces the LLMLingua-2 bidirectional encoder from the original blueprint.
Uses corpus-level unigram frequencies as a proxy for token importance — high
self-information tokens (rare words, proper nouns, numbers) are preserved;
low self-information tokens (stopwords, filler) are pruned.

Zero VRAM cost. Runs in milliseconds on CPU.

Critical entities (numbers, dates, proper nouns) are whitelisted and never
pruned regardless of their TF-IDF score. This ensures flight codes, city
names, and prices always survive.
"""

import math
import re
from pathlib import Path
from typing import Optional


# -----------------------------------------------------------------------------
# Built-in frequency table
# -----------------------------------------------------------------------------
# A minimal frequency table of the 200 most common English words. For the
# hackathon this is sufficient; in production we'd use a proper corpus like
# Google Web Trillion Word Corpus or COCA.
#
# Frequencies are approximate log probabilities: higher value = more common.

COMMON_WORDS = {
    "the": 7.0, "of": 6.5, "and": 6.4, "to": 6.3, "a": 6.2, "in": 6.0,
    "is": 5.9, "that": 5.7, "for": 5.6, "it": 5.5, "with": 5.4, "as": 5.3,
    "be": 5.2, "on": 5.2, "by": 5.1, "at": 5.0, "this": 5.0, "are": 4.9,
    "from": 4.8, "or": 4.8, "an": 4.7, "but": 4.6, "not": 4.6, "you": 4.5,
    "your": 4.5, "have": 4.4, "has": 4.3, "had": 4.2, "will": 4.2, "would": 4.1,
    "can": 4.1, "could": 4.0, "should": 4.0, "may": 3.9, "might": 3.8,
    "was": 4.5, "were": 4.3, "been": 4.0, "being": 3.7, "do": 4.3, "does": 4.0,
    "did": 3.9, "done": 3.6, "if": 4.3, "then": 4.0, "than": 3.9, "which": 4.2,
    "what": 4.3, "who": 4.0, "when": 4.1, "where": 4.0, "why": 3.8, "how": 4.2,
    "all": 4.2, "some": 4.0, "any": 3.9, "each": 3.7, "every": 3.6, "no": 4.0,
    "yes": 3.8, "so": 4.1, "also": 3.9, "only": 3.9, "just": 4.0, "now": 3.9,
    "get": 3.9, "got": 3.7, "go": 3.9, "going": 3.8, "come": 3.8, "want": 3.8,
    "need": 3.8, "like": 3.9, "see": 3.8, "look": 3.7, "please": 3.6,
    "thanks": 3.4, "thank": 3.5, "hello": 3.3, "hi": 3.4, "ok": 3.5, "okay": 3.5,
    "yeah": 3.2, "yep": 2.8, "sure": 3.4, "maybe": 3.4, "perhaps": 3.2,
    "there": 4.2, "here": 4.0, "these": 3.9, "those": 3.7, "them": 3.9,
    "their": 4.0, "they": 4.2, "he": 4.3, "she": 4.0, "his": 4.1, "her": 4.0,
    "we": 4.2, "our": 4.0, "us": 3.8, "my": 4.2, "me": 4.1, "i": 4.5,
    "about": 4.2, "into": 3.9, "over": 3.8, "under": 3.6, "through": 3.7,
    "between": 3.8, "after": 3.8, "before": 3.8, "during": 3.5, "while": 3.7,
    "because": 3.9, "since": 3.5, "until": 3.4, "although": 3.0, "though": 3.3,
    "however": 3.4, "therefore": 3.0, "thus": 2.9, "hence": 2.6, "indeed": 2.9,
    "really": 3.6, "very": 3.9, "quite": 3.4, "much": 3.9, "many": 3.9,
    "more": 4.1, "most": 3.9, "less": 3.7, "least": 3.4, "few": 3.5,
    "first": 3.9, "second": 3.5, "last": 3.8, "next": 3.7, "new": 4.1, "old": 3.7,
    "good": 3.9, "great": 3.7, "bad": 3.5, "best": 3.7, "worst": 3.0,
    "make": 3.9, "made": 3.8, "making": 3.5, "take": 3.8, "took": 3.6,
    "give": 3.6, "gave": 3.3, "find": 3.6, "found": 3.6, "know": 3.9,
    "knew": 3.4, "think": 3.8, "thought": 3.6, "say": 3.8, "said": 3.9,
    "tell": 3.6, "told": 3.5, "ask": 3.6, "asked": 3.5, "try": 3.6,
    "tried": 3.4, "use": 3.8, "used": 3.7, "work": 3.7, "worked": 3.4,
    "let": 3.6, "us": 3.6, "its": 3.8, "such": 3.5,
    # Travel-specific low-value filler
    "trip": 3.4, "travel": 3.5, "plan": 3.4, "planning": 3.3, "visit": 3.4,
    "going": 3.5, "want": 3.7, "would": 3.9, "looking": 3.3, "nice": 3.2,
}


class TFIDFPruner:
    """
    Scores tokens by self-information and prunes below a dynamic threshold.

    The scoring function:
        score(token) = -log(P(token))
    where P(token) is approximated by the frequency table. Unknown tokens
    (not in the table) get a high score (assumed rare = informative).

    Entity detection runs before scoring. Entities (proper nouns, numbers,
    dates, currency values) are whitelisted and assigned score=1.0 regardless
    of frequency.
    """

    def __init__(
        self,
        target_ratio: float = 0.60,
        min_score_for_keep: float = 0.35,
    ):
        """
        Args:
            target_ratio: Fraction of non-entity tokens to KEEP (0.60 = keep 60%).
            min_score_for_keep: Absolute floor — never prune above this score.
        """
        self.target_ratio = target_ratio
        self.min_score_for_keep = min_score_for_keep

        # Convert log-frequencies to self-information.
        # Higher log-freq => lower self-info => more prunable.
        # We normalize so that common words get score ~0.0 and rare words ~1.0.
        self.max_log_freq = max(COMMON_WORDS.values())
        self.unknown_score = 0.90   # Unknown tokens are probably domain-specific

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_and_prune(self, text: str) -> tuple[str, list[dict]]:
        """
        Takes a text string, returns (pruned_text, score_entries).

        `score_entries` is a list of per-token dicts suitable for the
        frontend heatmap — one entry per token in the original text.
        """
        tokens = self._tokenize_with_spans(text)
        if not tokens:
            return text, []

        # Score each token
        entries = []
        for tok_text, start, end in tokens:
            is_entity = self._is_entity(tok_text)
            if is_entity:
                score = 1.0
            else:
                score = self._score_token(tok_text)
            entries.append({
                "text": tok_text,
                "start": start,
                "end": end,
                "score": round(score, 3),
                "is_entity": is_entity,
                "preserved": False,   # filled in below
            })

        # Determine dynamic threshold from non-entity scores
        non_entity_scores = sorted(
            (e["score"] for e in entries if not e["is_entity"]),
            reverse=True,
        )
        if non_entity_scores:
            keep_count = int(len(non_entity_scores) * self.target_ratio)
            if keep_count < len(non_entity_scores):
                threshold = non_entity_scores[keep_count]
            else:
                threshold = 0.0
            threshold = max(threshold, 0.0)
        else:
            threshold = 0.0

        # Mark preservation
        for e in entries:
            if e["is_entity"]:
                e["preserved"] = True
            elif e["score"] >= threshold and e["score"] >= self.min_score_for_keep:
                e["preserved"] = True
            else:
                e["preserved"] = False

        # Reassemble preserved tokens
        kept_spans = [(e["start"], e["end"]) for e in entries if e["preserved"]]
        pruned_text = self._reassemble(text, kept_spans)

        return pruned_text, entries

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_token(self, token: str) -> float:
        """Compute normalized self-information for a token."""
        lower = token.lower()
        log_freq = COMMON_WORDS.get(lower)
        if log_freq is None:
            # Not in the frequency table — probably rare/domain-specific
            return self.unknown_score
        # Normalize: max_log_freq => 0.0 (highly prunable),
        #            low log_freq  => closer to 1.0 (less prunable)
        normalized = 1.0 - (log_freq / self.max_log_freq)
        return max(0.0, min(1.0, normalized))

    # ------------------------------------------------------------------
    # Entity detection (the whitelist)
    # ------------------------------------------------------------------

    _NUMERIC = re.compile(r"^\$?\d+[\d,.]*%?$")
    _DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    _FLIGHT_CODE = re.compile(r"^[A-Z]{2,3}\d{3,4}$")
    _CAPS_ABBREV = re.compile(r"^[A-Z]{2,6}$")   # e.g. "USD", "EUR", "JFK"

    def _is_entity(self, token: str) -> bool:
        """
        Is this token likely to be a critical entity that must be preserved?

        Heuristics (no neural model needed):
          - Numeric values ($3000, 14, 95%, 2026)
          - ISO dates (2026-05-01)
          - Flight codes (AF1234)
          - All-caps abbreviations (USD, JFK)
          - Capitalized words of length 2+ (likely proper nouns)
        """
        if not token:
            return False
        if self._NUMERIC.match(token):
            return True
        if self._DATE_ISO.match(token):
            return True
        if self._FLIGHT_CODE.match(token):
            return True
        if self._CAPS_ABBREV.match(token):
            return True
        # Capitalized word (first letter uppercase, rest lowercase or mixed)
        if len(token) >= 2 and token[0].isupper() and any(c.islower() for c in token):
            # Guard against sentence-start words like "The", "A"
            if token.lower() not in COMMON_WORDS:
                return True
        return False

    # ------------------------------------------------------------------
    # Tokenization
    # ------------------------------------------------------------------

    # Order matters: flight codes (letters+digits) must match BEFORE plain words
    # would grab just the letter portion.
    _TOKEN_RE = re.compile(r"[A-Z]{2,3}\d{3,4}|\$?\d+[\d,.]*%?|[A-Za-z]+(?:['-][A-Za-z]+)*")

    def _tokenize_with_spans(self, text: str) -> list[tuple[str, int, int]]:
        """Tokenize preserving original character spans for reassembly."""
        return [(m.group(), m.start(), m.end()) for m in self._TOKEN_RE.finditer(text)]

    def _reassemble(self, original: str, kept_spans: list[tuple[int, int]]) -> str:
        """
        Rebuild a text from preserved token spans, preserving inter-token
        whitespace only between adjacent preserved tokens.
        """
        if not kept_spans:
            return ""
        parts = []
        for i, (start, end) in enumerate(kept_spans):
            if i > 0:
                prev_end = kept_spans[i - 1][1]
                # If this token immediately followed the previous one in the
                # original text, preserve the exact separator. Otherwise,
                # insert a single space.
                gap = original[prev_end:start]
                if gap.strip() == "":
                    parts.append(gap if gap else " ")
                else:
                    parts.append(" ")
            parts.append(original[start:end])
        return "".join(parts)
