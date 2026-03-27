"""
Personalized guidance and investment recommendation engine.

Phase-1 upgrade over static rule-based logic:
- Context-aware recommendation prioritization
- Deterministic, testable scoring (no external model dependency)
- Backward-compatible response schema for existing frontend panels
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class UserFinanceProfile:
    income: float
    rent: float
    food: float
    travel: float
    shopping: float
    emi: float
    monthly_savings: float
    score: float
    expense_ratio: float
    savings_ratio: float
    emi_ratio: float


class PersonalizedGuidanceEngine:
    """Generates ranked guidance and investment suggestions."""

    @staticmethod
    def _safe_num(value) -> float:
        try:
            v = float(value)
            return v if v >= 0 else 0.0
        except Exception:
            return 0.0

    @classmethod
    def _build_profile(cls, data: Dict, score: float, patterns: Dict) -> UserFinanceProfile:
        income = cls._safe_num(data.get("income", 0))
        rent = cls._safe_num(data.get("rent", 0))
        food = cls._safe_num(data.get("food", 0))
        travel = cls._safe_num(data.get("travel", 0))
        shopping = cls._safe_num(data.get("shopping", 0))
        emi = cls._safe_num(data.get("emi", 0))
        monthly_savings = cls._safe_num(data.get("savings", 0))

        expense_ratio = cls._safe_num(patterns.get("expense_ratio", 0))
        savings_ratio = cls._safe_num(patterns.get("savings_ratio", 0))
        emi_ratio = cls._safe_num(patterns.get("emi_ratio", 0))

        return UserFinanceProfile(
            income=income,
            rent=rent,
            food=food,
            travel=travel,
            shopping=shopping,
            emi=emi,
            monthly_savings=monthly_savings,
            score=cls._safe_num(score),
            expense_ratio=expense_ratio,
            savings_ratio=savings_ratio,
            emi_ratio=emi_ratio,
        )

    @staticmethod
    def _top_spending_categories(profile: UserFinanceProfile) -> List[Tuple[str, float]]:
        categories = [
            ("rent", profile.rent),
            ("food", profile.food),
            ("travel", profile.travel),
            ("shopping", profile.shopping),
            ("emi", profile.emi),
        ]
        categories.sort(key=lambda x: x[1], reverse=True)
        return [(k, v) for k, v in categories if v > 0][:2]

    @classmethod
    def generate_guidance(cls, data: Dict, score: float, patterns: Dict) -> Dict:
        profile = cls._build_profile(data, score, patterns)

        guidance = {
            "recommendations": [],
            "strengths": [],
            "warnings": [],
        }

        ranked_recommendations: List[Tuple[int, str]] = []

        # Strengths
        if profile.savings_ratio >= 0.25:
            guidance["strengths"].append("Excellent savings habit. You are saving 25%+ of your income.")
        elif profile.savings_ratio >= 0.15:
            guidance["strengths"].append("Good savings discipline. Keep maintaining this consistency.")

        if profile.emi_ratio == 0:
            guidance["strengths"].append("No EMI burden. This gives you flexibility to build wealth faster.")

        if profile.expense_ratio <= 0.55:
            guidance["strengths"].append("Healthy expense control. Your spending is within a sustainable range.")

        # Warnings + ranked recommendations
        if profile.expense_ratio > 1.0:
            guidance["warnings"].append("Critical deficit: your total monthly outflow is higher than your income.")
            ranked_recommendations.append((100, "Immediately cut non-essential expenses and pause discretionary purchases for 30 days."))
        elif profile.expense_ratio > 0.8:
            guidance["warnings"].append("High burn rate: over 80% of income is being consumed by expenses.")
            ranked_recommendations.append((85, "Target reducing total expenses below 70% of income over the next 2 months."))
        elif profile.expense_ratio > 0.6:
            ranked_recommendations.append((65, "Aim to bring total expenses under 60% of income to accelerate savings."))

        if profile.savings_ratio < 0.05:
            guidance["warnings"].append("Very low savings rate. Build at least a 10% monthly savings habit.")
            ranked_recommendations.append((90, "Automate savings transfer on salary day before other spending."))
        elif profile.savings_ratio < 0.10:
            ranked_recommendations.append((70, "Increase monthly savings to at least 10-15% of income."))

        if profile.emi_ratio > 0.4:
            guidance["warnings"].append("Debt stress detected: EMI exceeds 40% of monthly income.")
            ranked_recommendations.append((95, "Prioritize high-interest debt repayment and avoid taking new loans."))
        elif profile.emi_ratio > 0.3:
            ranked_recommendations.append((75, "Consider debt consolidation or refinancing to lower EMI burden."))

        top_spend = cls._top_spending_categories(profile)
        for category, amount in top_spend:
            if profile.income <= 0:
                continue
            ratio = amount / profile.income
            if category == "rent" and ratio > 0.35:
                ranked_recommendations.append((72, "Housing cost is high. Explore reducing rent or sharing accommodation."))
            if category == "shopping" and ratio > 0.12:
                ranked_recommendations.append((68, "Set a fixed monthly cap for shopping and track discretionary purchases weekly."))
            if category == "food" and ratio > 0.20:
                ranked_recommendations.append((62, "Optimize food spending with a weekly budget and meal planning."))

        if profile.score < 35:
            ranked_recommendations.append((98, "Create a strict zero-based budget and review spending every week."))
        elif profile.score < 50:
            ranked_recommendations.append((78, "Build a starter emergency buffer and reduce top two expense categories."))
        elif profile.score >= 80:
            guidance["strengths"].append("Strong financial base. You can consider long-term wealth acceleration strategies.")
            ranked_recommendations.append((55, "Increase SIP amount gradually as income grows to compound long-term gains."))

        # Deduplicate + top 5
        seen = set()
        ordered = []
        for _, rec in sorted(ranked_recommendations, key=lambda x: x[0], reverse=True):
            if rec not in seen:
                seen.add(rec)
                ordered.append(rec)

        guidance["recommendations"] = ordered[:5]
        return guidance

    @classmethod
    def suggest_investments(cls, score: float, data: Dict, patterns: Dict) -> Dict:
        profile = cls._build_profile(data, score, patterns)

        monthly_savings = int(profile.monthly_savings)
        investable = max(0, monthly_savings)

        # Readiness gating
        eligible = profile.score >= 50 and profile.savings_ratio >= 0.10 and profile.emi_ratio < 0.5 and investable > 0

        # Build a deterministic investment readiness index for personalization.
        readiness_index = (
            profile.score * 0.5
            + max(0.0, min(1.0, profile.savings_ratio / 0.25)) * 30
            + max(0.0, 1.0 - min(1.0, profile.emi_ratio / 0.5)) * 20
        )

        suggestions: List[Dict] = []

        if not eligible:
            suggestions.append({
                "type": "Emergency Fund (Savings / Liquid Fund)",
                "risk_level": "Very Low",
                "allocation": investable,
                "description": "Stabilize cash flow and build a safety buffer before growth investing.",
                "suitable": True,
            })
            suggestions.append({
                "type": "High-Risk Equity Allocation",
                "risk_level": "High",
                "allocation": 0,
                "description": "Delay high-risk investing until savings consistency and EMI burden improve.",
                "suitable": False,
            })
        else:
            if readiness_index >= 80:
                allocation = {
                    "Equity Index / Flexi-cap Funds": 0.55,
                    "Debt / PPF": 0.25,
                    "Liquid / Emergency Buffer": 0.20,
                }
                risk_level = "Medium to High"
            elif readiness_index >= 65:
                allocation = {
                    "Hybrid Mutual Funds": 0.45,
                    "Debt / PPF": 0.35,
                    "Liquid / Emergency Buffer": 0.20,
                }
                risk_level = "Medium"
            else:
                allocation = {
                    "Conservative Hybrid / Debt Funds": 0.40,
                    "Recurring Deposit / PPF": 0.40,
                    "Liquid / Emergency Buffer": 0.20,
                }
                risk_level = "Low to Medium"

            for name, weight in allocation.items():
                suggestions.append({
                    "type": name,
                    "risk_level": risk_level if "Liquid" not in name and "Recurring" not in name else "Low",
                    "allocation": int(investable * weight),
                    "description": "Allocation personalized using your score, savings consistency, and debt pressure.",
                    "suitable": True,
                })

        message = cls.get_investment_advice(profile.score)

        return {
            "eligible": eligible,
            "suggestions": suggestions,
            "message": message,
            "advice": message,
        }

    @staticmethod
    def get_investment_advice(score: float) -> str:
        if score >= 80:
            return "Strong financial health. Use a diversified growth strategy with disciplined SIPs."
        if score >= 65:
            return "Good financial position. Balance growth and stability through diversified allocation."
        if score >= 50:
            return "You can begin with moderate-risk, diversified investing while strengthening emergency reserves."
        if score >= 35:
            return "Prioritize emergency cushion and debt control before increasing investment risk."
        return "Focus on cash-flow stability and debt reduction first. Investment can follow after financial recovery."
