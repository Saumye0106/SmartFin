"""
nudge_generator.py — Convert anomaly scores and patterns into human-readable nudges.

Generates contextual, actionable nudge messages with severity levels,
appropriate emoji, and specific numbers from the user's own data.
"""

from __future__ import annotations

from typing import Dict, List, Optional


CAT_DISPLAY = {
    "food_groceries": "Food & Groceries",
    "travel_transport": "Travel & Transport",
    "shopping_entertainment": "Shopping & Entertainment",
    "rent_housing": "Rent & Housing",
    "emi_loans": "EMI & Loans",
    "healthcare": "Healthcare",
    "utilities": "Utilities",
    "other": "Other",
}

SEVERITY_CONFIG = {
    "high":   {"emoji": "🔴", "color": "red",    "label": "High Alert"},
    "medium": {"emoji": "🟡", "color": "amber",  "label": "Watch Out"},
    "low":    {"emoji": "🟢", "color": "green",  "label": "Heads Up"},
}


class NudgeGenerator:
    """Translates anomaly detector output into user-facing nudge cards."""

    def generate_nudges(
        self,
        anomalous_weeks: List[Dict],
        patterns: List[Dict],
        budget_bust_prob: Optional[float],
        weeks_of_data: int,
    ) -> List[Dict]:
        """
        Generate a deduplicated, ranked list of nudge cards.

        Args:
            anomalous_weeks: From AnomalyDetector.get_top_anomalous_weeks()
            patterns: From AnomalyDetector.get_patterns()
            budget_bust_prob: float 0–1 or None
            weeks_of_data: Total weeks of expense history

        Returns:
            List of nudge dicts sorted by severity (high → low)
        """
        nudges: List[Dict] = []
        seen_categories: set = set()

        # 1. Budget-bust probability nudge (if available)
        if budget_bust_prob is not None:
            if budget_bust_prob >= 0.65:
                nudges.append(self._budget_bust_nudge(budget_bust_prob, "high"))
            elif budget_bust_prob >= 0.40:
                nudges.append(self._budget_bust_nudge(budget_bust_prob, "medium"))

        # 2. Anomalous week nudges (current week / most recent)
        for week_data in anomalous_weeks:
            for cat_signal in week_data["top_categories"]:
                cat = cat_signal["category"]
                ratio = cat_signal["ratio_vs_avg"]
                score = week_data["anomaly_score"]
                severity = week_data["severity"]

                if cat in seen_categories:
                    continue
                seen_categories.add(cat)

                nudge = self._anomaly_nudge(cat, ratio, week_data["week_start"], severity, score)
                nudges.append(nudge)

        # 3. Pattern nudges
        for pattern in patterns:
            cat = pattern["category"]
            if cat in seen_categories:
                continue
            seen_categories.add(f"pattern_{cat}")
            nudges.append(self._pattern_nudge(pattern))

        # 4. If no nudges (user is doing well)
        if not nudges:
            nudges.append({
                "id": "all_clear",
                "severity": "low",
                "emoji": "✅",
                "color": "green",
                "label": "Heads Up",
                "category": None,
                "title": "Spending looks normal",
                "message": (
                    f"Your spending patterns across all categories look consistent "
                    f"with your {weeks_of_data}-week history. Keep it up!"
                ),
                "action": None,
            })

        # Sort: high → medium → low
        severity_order = {"high": 0, "medium": 1, "low": 2}
        nudges.sort(key=lambda n: severity_order.get(n["severity"], 3))

        return nudges[:8]  # Cap at 8 nudges

    # ── Nudge builders ────────────────────────────────────────────────────

    def _budget_bust_nudge(self, prob: float, severity: str) -> Dict:
        cfg = SEVERITY_CONFIG[severity]
        pct = int(prob * 100)
        return {
            "id": "budget_bust",
            "severity": severity,
            "emoji": cfg["emoji"],
            "color": cfg["color"],
            "label": cfg["label"],
            "category": "overall",
            "title": f"{pct}% chance of exceeding budget this month",
            "message": (
                f"Based on your spending trajectory so far, our model estimates a "
                f"{pct}% probability that you'll exceed your monthly budget. "
                f"You still have time to course-correct."
            ),
            "action": "Review your biggest expense categories below.",
        }

    def _anomaly_nudge(
        self, category: str, ratio: float, week_start: str, severity: str, score: float
    ) -> Dict:
        cfg = SEVERITY_CONFIG[severity]
        display_cat = CAT_DISPLAY.get(category, category.replace("_", " ").title())
        pct_over = int((ratio - 1) * 100)

        if ratio >= 2.5:
            msg = (
                f"You've spent {ratio:.1f}x your usual amount on {display_cat} this week — "
                f"that's {pct_over}% above your personal average."
            )
        elif ratio >= 1.5:
            msg = (
                f"{display_cat} spending is {pct_over}% above your 4-week average this week. "
                f"This is flagged as unusual by your personal spending model."
            )
        else:
            msg = (
                f"{display_cat} spending is trending slightly above your usual pattern "
                f"({pct_over}% over average)."
            )

        return {
            "id": f"anomaly_{category}",
            "severity": severity,
            "emoji": cfg["emoji"],
            "color": cfg["color"],
            "label": cfg["label"],
            "category": display_cat,
            "title": f"Unusual {display_cat} spending detected",
            "message": msg,
            "action": f"Check if this is a one-time expense or a new recurring pattern.",
            "anomaly_score": round(score, 3),
            "ratio_vs_avg": round(ratio, 2),
        }

    def _pattern_nudge(self, pattern: Dict) -> Dict:
        cfg = SEVERITY_CONFIG["medium"]
        display_cat = CAT_DISPLAY.get(pattern["category"],
                                      pattern["category"].replace("_", " ").title())
        return {
            "id": f"pattern_{pattern['category']}",
            "severity": "medium",
            "emoji": "📊",
            "color": "blue",
            "label": "Recurring Pattern",
            "category": display_cat,
            "title": f"Pattern detected in {display_cat}",
            "message": pattern["description"],
            "action": (
                f"Consider pre-allocating a budget for {display_cat} "
                f"at the start of each month to stay on track."
            ),
        }
