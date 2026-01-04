from typing import Dict, Any, List
import pandas as pd

class BusinessFormatter:
    """Formats outputs for non-technical business users"""
    
    def get_data_understanding(self, df, domain: str, columns: List[str]) -> Dict[str, str]:
        """Generate simple explanation of what the data is about"""
        row_count = len(df)
        domain_purposes = {
            "HR": "employee information and workforce data",
            "Finance": "financial transactions and budget information",
            "Sales": "sales performance and customer data",
            "Operations": "operational efficiency and process data",
            "General": "business data"
        }
        
        purpose = domain_purposes.get(domain, "business data")
        
        # Identify key columns for context
        key_columns = columns[:5]  # First 5 columns
        
        understanding = {
            "what_is_this": f"This dataset contains {purpose} with {row_count:,} records. "
                           f"It includes information about {', '.join(key_columns[:3])} and other related fields.",
            "why_important": f"Analyzing this {domain.lower()} data helps identify patterns and trends that can "
                            f"support better business decisions, such as understanding relationships between "
                            f"different factors and predicting future outcomes."
        }
        
        return understanding
    
    def format_confidence_level(self, confidence: float) -> str:
        """Convert numeric confidence to Low/Medium/High"""
        if confidence >= 0.7:
            return "High"
        elif confidence >= 0.4:
            return "Medium"
        else:
            return "Low"
    
    def format_prediction_range(self, value: Any, is_classification: bool, 
                               target_column: str = "") -> str:
        """Convert prediction value to Low/Medium/High range"""
        if is_classification:
            # For classification, return as-is or convert to Likely/Unlikely
            value_str = str(value).lower()
            if value_str in ['yes', 'true', '1', 'high']:
                return "High"
            elif value_str in ['no', 'false', '0', 'low']:
                return "Low"
            else:
                return str(value)
        else:
            # For regression, convert to range
            try:
                num_value = float(value)
                
                # Use domain-specific thresholds if available
                if 'salary' in target_column.lower() or 'amount' in target_column.lower():
                    if num_value < 30000:
                        return "Low"
                    elif num_value < 60000:
                        return "Medium"
                    else:
                        return "High"
                elif 'count' in target_column.lower() or 'quantity' in target_column.lower():
                    # Need to calculate percentiles from data
                    return f"{num_value:.0f}"  # Return number for now
                else:
                    # Generic range based on value
                    if num_value < 0:
                        return "Low"
                    elif num_value < 100:
                        return "Medium"
                    else:
                        return "High"
            except:
                return str(value)
    
    def get_relationships_explanation(self, feature_impact: Dict[str, float], 
                                     domain: str) -> List[str]:
        """Explain relationships between columns in simple terms"""
        relationships = []
        
        # Sort by importance
        sorted_features = sorted(feature_impact.items(), key=lambda x: x[1], reverse=True)
        
        top_features = sorted_features[:5]
        
        for feature, importance in top_features:
            impact_level = "strongly" if importance > 0.3 else "moderately" if importance > 0.15 else "slightly"
            relationships.append(
                f"{feature} {impact_level} influences the outcome, with {importance*100:.1f}% impact"
            )
        
        return relationships
    
    def highlight_key_rules(self, rules: List[Dict[str, Any]], max_rules: int = 5) -> List[Dict[str, Any]]:
        """Select and highlight the most important business rules"""
        if not rules:
            return []
        
        # Sort by confidence and impact
        def rule_score(rule):
            confidence = rule.get("confidence", 0.0)
            impact = rule.get("impact", "low")
            impact_score = {"high": 3, "medium": 2, "low": 1}.get(impact.lower(), 1)
            return confidence * impact_score
        
        sorted_rules = sorted(rules, key=rule_score, reverse=True)
        return sorted_rules[:max_rules]
    
    def generate_summary(self, domain: str, model_metrics: Dict[str, Any],
                        key_rules: List[Dict[str, Any]], 
                        relationships: List[str],
                        data_issues: List[str] = None) -> Dict[str, Any]:
        """Generate user-friendly summary"""
        summary = {
            "what_we_learned": [],
            "what_to_do_next": [],
            "limitations": []
        }
        
        # What we learned
        summary["what_we_learned"].append(
            f"Analyzed {domain} data and identified key patterns and relationships."
        )
        
        if key_rules:
            summary["what_we_learned"].append(
                f"Found {len(key_rules)} important business rules that explain how different factors affect outcomes."
            )
        
        if relationships:
            top_relationship = relationships[0] if relationships else ""
            summary["what_we_learned"].append(
                f"Key finding: {top_relationship}"
            )
        
        # What to do next
        if model_metrics.get("accuracy", 0) > 0.8:
            summary["what_to_do_next"].append(
                "The model shows good accuracy. You can use these predictions to make informed business decisions."
            )
        else:
            summary["what_to_do_next"].append(
                "Consider collecting more data or additional features to improve prediction accuracy."
            )
        
        if key_rules:
            summary["what_to_do_next"].append(
                "Use the highlighted business rules to understand what factors drive your outcomes and adjust strategies accordingly."
            )
        
        # Limitations
        if data_issues:
            summary["limitations"].extend(data_issues)
        else:
            summary["limitations"].append(
                "Analysis is based on available data. Results may vary with new data or changing conditions."
            )
        
        if model_metrics.get("accuracy", 0) < 0.7:
            summary["limitations"].append(
                "Prediction accuracy is moderate. Use predictions as guidance rather than absolute certainty."
            )
        
        return summary

