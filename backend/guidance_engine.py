"""
Personalized guidance and investment recommendation engine.

Phase-1 upgrade over static rule-based logic:
- Context-aware recommendation prioritization
- Deterministic, testable scoring (no external model dependency)
- Backward-compatible response schema for existing frontend panels
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from typing import Dict, List, Tuple

try:
    import boto3
except Exception:  # pragma: no cover - optional at runtime
    boto3 = None


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
    def _ai_enabled() -> bool:
        """Feature-flag AI guidance; enabled by default with graceful fallback."""
        return os.environ.get("SMARTFIN_AI_GUIDANCE_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}

    @staticmethod
    def _model_id() -> str:
        return os.environ.get("SMARTFIN_GUIDANCE_MODEL_ID") or os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")

    @staticmethod
    def _bedrock_region() -> str:
        return os.environ.get("AWS_REGION", "us-east-1")

    @classmethod
    def _invoke_bedrock_json(cls, prompt: str, max_tokens: int = 900) -> Dict | None:
        """Call Bedrock and parse a JSON object from response text."""
        if not cls._ai_enabled() or boto3 is None:
            return None

        try:
            client = boto3.client("bedrock-runtime", region_name=cls._bedrock_region())
            response = client.converse(
                modelId=cls._model_id(),
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": 0.2,
                    "topP": 0.9,
                },
            )

            text = ""
            blocks = (((response or {}).get("output") or {}).get("message") or {}).get("content", [])
            for block in blocks:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    text += block["text"]

            if not text.strip():
                return None

            # Handle direct JSON and fenced JSON.
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"\\s*```$", "", cleaned)

            try:
                parsed = json.loads(cleaned)
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                match = re.search(r"\{[\s\S]*\}", text)
                if not match:
                    return None
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    @staticmethod
    def _sanitize_guidance_shape(payload: Dict | None) -> Dict | None:
        if not isinstance(payload, dict):
            return None
        recs = payload.get("recommendations", [])
        strengths = payload.get("strengths", [])
        warnings = payload.get("warnings", [])
        if not isinstance(recs, list) or not isinstance(strengths, list) or not isinstance(warnings, list):
            return None
        return {
            "recommendations": [str(x).strip() for x in recs if str(x).strip()][:6],
            "strengths": [str(x).strip() for x in strengths if str(x).strip()][:6],
            "warnings": [str(x).strip() for x in warnings if str(x).strip()][:6],
        }

    @staticmethod
    def _sanitize_investment_shape(payload: Dict | None) -> Dict | None:
        if not isinstance(payload, dict):
            return None
        eligible = bool(payload.get("eligible", False))
        suggestions = payload.get("suggestions", [])
        message = str(payload.get("message", "")).strip()
        advice = str(payload.get("advice", "")).strip() or message
        if not isinstance(suggestions, list):
            return None

        normalized = []
        for s in suggestions[:8]:
            if not isinstance(s, dict):
                continue
            normalized.append(
                {
                    "type": str(s.get("type", "")).strip() or "Investment Option",
                    "risk_level": str(s.get("risk_level", "Medium")).strip() or "Medium",
                    "allocation": int(float(s.get("allocation", 0) or 0)),
                    "description": str(s.get("description", "")).strip() or "Personalized recommendation based on financial profile.",
                    "suitable": bool(s.get("suitable", True)),
                }
            )

        return {
            "eligible": eligible,
            "suggestions": normalized,
            "message": message or "Personalized investment guidance generated from your financial profile.",
            "advice": advice or "Personalized investment guidance generated from your financial profile.",
        }

    @classmethod
    def _ai_guidance(cls, data: Dict, score: float, patterns: Dict) -> Dict | None:
        prompt = (
            "You are a senior financial planning assistant for Indian users. "
            "Generate concise, high-impact, data-grounded guidance. "
            "Return ONLY valid JSON with keys: recommendations (list of strings), strengths (list of strings), warnings (list of strings). "
            "No markdown, no extra keys, no prose outside JSON.\\n\\n"
            f"financial_score: {float(score):.2f}\\n"
            f"user_data: {json.dumps(data, ensure_ascii=True)}\\n"
            f"spending_patterns: {json.dumps(patterns, ensure_ascii=True)}\\n\\n"
            "Rules:\\n"
            "- Recommendations must be actionable and specific (include numbers/percentages where possible).\\n"
            "- Keep each line under 140 chars.\\n"
            "- Prioritize debt stress, savings consistency, and expense concentration.\\n"
            "- Maximum 5 recommendations, 4 strengths, 4 warnings."
        )
        return cls._sanitize_guidance_shape(cls._invoke_bedrock_json(prompt, max_tokens=700))

    @classmethod
    def _ai_investments(cls, score: float, data: Dict, patterns: Dict) -> Dict | None:
        prompt = (
            "You are a senior investment advisor for Indian users. "
            "Generate personalized investment recommendations from user's cashflow and risk signals. "
            "Return ONLY valid JSON with keys: eligible (boolean), suggestions (list), message (string), advice (string). "
            "Each suggestion must be an object with keys: type, risk_level, allocation, description, suitable. "
            "No markdown, no extra keys.\\n\\n"
            f"financial_score: {float(score):.2f}\\n"
            f"user_data: {json.dumps(data, ensure_ascii=True)}\\n"
            f"spending_patterns: {json.dumps(patterns, ensure_ascii=True)}\\n\\n"
            "Rules:\\n"
            "- Allocate monthly savings amount intelligently across 2-4 buckets.\\n"
            "- If score is weak or debt burden is high, recommend capital-protection first.\\n"
            "- Keep message and advice concise and practical."
        )
        return cls._sanitize_investment_shape(cls._invoke_bedrock_json(prompt, max_tokens=900))

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
    def generate_guidance(cls, data: Dict, score: float, patterns: Dict, return_meta: bool = False):
        ai_guidance = cls._ai_guidance(data, score, patterns)
        if ai_guidance:
            if return_meta:
                return ai_guidance, {"source": "ai", "engine": "bedrock"}
            return ai_guidance

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
        if return_meta:
            return guidance, {"source": "fallback", "engine": "deterministic"}
        return guidance

    @classmethod
    def generate_guidance_ai(cls, data: Dict, score: float, patterns: Dict, return_meta: bool = False):
        """AI-first guidance API with deterministic fallback."""
        return cls.generate_guidance(data, score, patterns, return_meta=return_meta)

    @classmethod
    def suggest_investments(cls, score: float, data: Dict, patterns: Dict, return_meta: bool = False):
        ai_investments = cls._ai_investments(score, data, patterns)
        if ai_investments:
            if return_meta:
                return ai_investments, {"source": "ai", "engine": "bedrock"}
            return ai_investments

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

        fallback_result = {
            "eligible": eligible,
            "suggestions": suggestions,
            "message": message,
            "advice": message,
        }
        if return_meta:
            return fallback_result, {"source": "fallback", "engine": "deterministic"}
        return fallback_result

    @classmethod
    def suggest_investments_ai(cls, score: float, data: Dict, patterns: Dict, return_meta: bool = False):
        """AI-first investments API with deterministic fallback."""
        return cls.suggest_investments(score, data, patterns, return_meta=return_meta)

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
