from typing import Dict, Any, List, Optional


class RiskEngine:
    """
    Derives high-level business risks and insights from rules and data.

    Focus areas:
    - Attrition risk (mainly HR / Education with people-related data)
    - Cost risk (Finance / Sales with budget, expense, or loss signals)
    - Performance risk (any domain with targets vs outcomes or efficiency)

    All internal calculations are rule-based and explainable; only
    human-readable outputs are exposed to the caller.
    """

    def analyze(
        self,
        df,
        domain: str,
        rules_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Produce overall risk levels and narrative insights."""
        if rules_data is None:
            rules_data = {"association_rules": [], "if_then_rules": [], "summary": {}}

        if_then_rules: List[Dict[str, Any]] = rules_data.get("if_then_rules", [])
        assoc_rules: List[Dict[str, Any]] = rules_data.get("association_rules", [])

        # Derive risk levels from rule texts and impact flags
        attrition_risk = self._derive_attrition_risk(domain, if_then_rules, assoc_rules)
        cost_risk = self._derive_cost_risk(domain, if_then_rules, assoc_rules)
        performance_risk = self._derive_performance_risk(domain, if_then_rules, assoc_rules)

        risk_levels = {
            "attrition_risk": attrition_risk,
            "cost_risk": cost_risk,
            "performance_risk": performance_risk,
        }

        # Global confidence for the whole analysis
        confidence_level = self._overall_confidence(domain, rules_data)

        # Build concise insights and recommendations
        insights = self._build_insights(domain, risk_levels, if_then_rules, assoc_rules)
        recommendations = self._build_recommendations(domain, risk_levels)

        # If we really have little signal, call it out clearly
        limitations = None
        if confidence_level == "Low":
            limitations = (
                "The dataset does not strongly match a specific business domain, "
                "so the risk assessment should be treated as indicative rather than definitive."
            )

        return {
            "domain": domain,
            "risk_levels": risk_levels,
            "confidence_level": confidence_level,
            "insights": insights,
            "recommendations": recommendations,
            "limitations": limitations,
            "sample_rule_count": {
                "if_then_rules": len(if_then_rules),
                "association_rules": len(assoc_rules),
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _derive_attrition_risk(
        self,
        domain: str,
        if_then_rules: List[Dict[str, Any]],
        assoc_rules: List[Dict[str, Any]],
    ) -> str:
        """Map HR-style rules into an overall attrition risk level."""
        domain_lower = (domain or "").lower()
        relevant = domain_lower in ("hr", "education")

        text_hits_high = 0
        text_hits_medium = 0

        def scan_rules(rules: List[Dict[str, Any]]) -> None:
            nonlocal text_hits_high, text_hits_medium
            for r in rules:
                txt = str(r.get("rule", "")).lower()
                impact = str(r.get("impact", "")).lower()
                if any(x in txt for x in ["attrition", "churn", "resignation", "leave"]):
                    if "high" in txt or impact == "high":
                        text_hits_high += 1
                    elif "medium" in txt or impact == "medium":
                        text_hits_medium += 1

        scan_rules(if_then_rules)
        scan_rules(assoc_rules)

        if not relevant and text_hits_high == 0 and text_hits_medium == 0:
            return "Not applicable"

        if text_hits_high >= 2:
            return "High"
        if text_hits_high == 1 or text_hits_medium >= 2:
            return "Medium"
        if text_hits_medium == 1:
            return "Low"
        return "Not enough information"

    def _derive_cost_risk(
        self,
        domain: str,
        if_then_rules: List[Dict[str, Any]],
        assoc_rules: List[Dict[str, Any]],
    ) -> str:
        """Estimate cost / budget risk from finance-style rules."""
        domain_lower = (domain or "").lower()
        relevant = domain_lower in ("finance", "sales", "general")

        high_flags = 0
        medium_flags = 0

        keywords = [
            "expense",
            "cost",
            "budget",
            "overrun",
            "loss",
            "overspend",
        ]

        def scan(rules: List[Dict[str, Any]]) -> None:
            nonlocal high_flags, medium_flags
            for r in rules:
                txt = str(r.get("rule", "")).lower()
                if any(k in txt for k in keywords):
                    impact = str(r.get("impact", "")).lower()
                    if "high" in txt or impact == "high":
                        high_flags += 1
                    elif "medium" in txt or impact == "medium":
                        medium_flags += 1

        scan(if_then_rules)
        scan(assoc_rules)

        if not relevant and high_flags == 0 and medium_flags == 0:
            return "Not applicable"

        if high_flags >= 2:
            return "High"
        if high_flags == 1 or medium_flags >= 2:
            return "Medium"
        if medium_flags == 1:
            return "Low"
        return "Not enough information"

    def _derive_performance_risk(
        self,
        domain: str,
        if_then_rules: List[Dict[str, Any]],
        assoc_rules: List[Dict[str, Any]],
    ) -> str:
        """Estimate performance / target achievement risk."""
        high_flags = 0
        medium_flags = 0

        keywords = [
            "performance",
            "target",
            "efficiency",
            "productivity",
            "score",
            "grade",
        ]

        def scan(rules: List[Dict[str, Any]]) -> None:
            nonlocal high_flags, medium_flags
            for r in rules:
                txt = str(r.get("rule", "")).lower()
                if any(k in txt for k in keywords):
                    impact = str(r.get("impact", "")).lower()
                    if "high" in txt or impact == "high":
                        high_flags += 1
                    elif "medium" in txt or impact == "medium":
                        medium_flags += 1

        scan(if_then_rules)
        scan(assoc_rules)

        if high_flags >= 2:
            return "High"
        if high_flags == 1 or medium_flags >= 2:
            return "Medium"
        if medium_flags == 1:
            return "Low"
        return "Not enough information"

    def _overall_confidence(self, domain: str, rules_data: Dict[str, Any]) -> str:
        """Summarise how reliable the overall interpretation is."""
        domain_lower = (domain or "").lower()
        assoc_count = len(rules_data.get("association_rules", []) or [])
        if_then_count = len(rules_data.get("if_then_rules", []) or [])
        total_rules = assoc_count + if_then_count

        if domain_lower == "general" or total_rules == 0:
            return "Low"
        if total_rules < 5:
            return "Medium"
        return "High"

    def _build_insights(
        self,
        domain: str,
        risk_levels: Dict[str, str],
        if_then_rules: List[Dict[str, Any]],
        assoc_rules: List[Dict[str, Any]],
    ) -> List[str]:
        """Convert rule patterns and risk levels into short insights."""
        insights: List[str] = []

        attr = risk_levels.get("attrition_risk")
        cost = risk_levels.get("cost_risk")
        perf = risk_levels.get("performance_risk")

        if attr in ("High", "Medium"):
            insights.append(
                "Patterns in the data suggest that people-related risk is elevated, "
                "especially for groups with weaker attendance or higher leave usage."
            )
        if cost in ("High", "Medium"):
            insights.append(
                "Spending and budget-related patterns point to potential cost pressure "
                "in certain segments or time periods."
            )
        if perf in ("High", "Medium"):
            insights.append(
                "Performance or target-achievement patterns indicate areas where execution "
                "could be strengthened to avoid slippage."
            )

        # If no specific risk is clearly elevated, still give a constructive remark
        if not insights:
            insights.append(
                "The dataset does not show a clear concentration of risk in one specific area; "
                "current patterns look relatively balanced, but deeper drill-down may still be useful."
            )

        # Add 2–3 of the strongest rules as narrative support (without metrics)
        human_rules: List[str] = []
        for r in (if_then_rules or [])[:3]:
            text = str(r.get("rule", "")).strip()
            if text:
                human_rules.append(text)
        for r in (assoc_rules or [])[:2]:
            text = str(r.get("rule", "")).strip()
            if text:
                human_rules.append(text)

        if human_rules:
            insights.append(
                "Some of the strongest patterns behind these insights include: "
                + "; ".join(human_rules)
                + "."
            )

        return insights

    def _build_recommendations(
        self,
        domain: str,
        risk_levels: Dict[str, str],
    ) -> List[str]:
        """Produce domain-aware, practical recommendations."""
        recs: List[str] = []
        domain_lower = (domain or "").lower()

        attr = risk_levels.get("attrition_risk")
        cost = risk_levels.get("cost_risk")
        perf = risk_levels.get("performance_risk")

        # Attrition / people risk
        if attr in ("High", "Medium"):
            recs.append(
                "Focus on groups with low attendance or frequent leave and engage them "
                "through manager check-ins, workload review, and clear growth plans."
            )

        # Cost risk
        if cost in ("High", "Medium"):
            recs.append(
                "Review high-cost items and cost centers that often trigger rules, and put simple "
                "budget alerts or approval thresholds in place for those areas."
            )

        # Performance risk
        if perf in ("High", "Medium"):
            recs.append(
                "Identify teams or segments where targets are frequently missed and provide additional "
                "support, training, or process simplification to close the gap."
            )

        # Domain-specific advice
        if domain_lower == "hr":
            recs.append(
                "For HR data, consider combining attendance, tenure, and satisfaction information to "
                "prioritise which employees or roles need proactive retention actions."
            )
        elif domain_lower == "finance":
            recs.append(
                "For Finance data, align expense patterns with budget plans at a monthly level so that "
                "variances are spotted early rather than at quarter-end."
            )
        elif domain_lower == "sales":
            recs.append(
                "For Sales data, track conversion, pipeline quality, and win/loss patterns regularly "
                "to keep performance risk under control."
            )
        elif domain_lower == "education":
            recs.append(
                "For Education data, combine attendance, marks, and course difficulty to identify "
                "students who may need early academic support."
            )

        if not recs:
            recs.append(
                "Use the strongest rules as simple business checks, and monitor them periodically to "
                "see whether risk is increasing or decreasing over time."
            )

        return recs


