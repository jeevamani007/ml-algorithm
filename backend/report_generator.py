import pandas as pd
from typing import Dict, Any
from datetime import datetime
from business_formatter import BusinessFormatter

class ReportGenerator:
    """Generates comprehensive reports"""
    
    def generate(self, dataset_id: str, dataset_info: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Generate comprehensive report"""
        try:
            report = {
                "report_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "dataset_id": dataset_id,
                "domain": domain,
                "generated_at": datetime.now().isoformat(),
                "sections": {}
            }
            
            # 1. Dataset Summary
            try:
                report["sections"]["dataset_summary"] = self._generate_dataset_summary(dataset_info)
            except Exception as e:
                report["sections"]["dataset_summary"] = {"error": f"Could not generate dataset summary: {str(e)}"}
            
            # 2. Domain Detection
            try:
                if "detected_domains" in dataset_info:
                    report["sections"]["domain_detection"] = {
                        "detected_domains": dataset_info.get("detected_domains", []),
                        "primary_domain": domain
                    }
            except Exception as e:
                report["sections"]["domain_detection"] = {"error": f"Could not generate domain detection: {str(e)}"}
            
            # 3. Preprocessing Summary
            try:
                if "preprocessed_data" in dataset_info and domain in dataset_info.get("preprocessed_data", {}):
                    report["sections"]["preprocessing"] = dataset_info["preprocessed_data"][domain].get("info", {})
            except Exception as e:
                report["sections"]["preprocessing"] = {"error": f"Could not generate preprocessing info: {str(e)}"}
            
            # 4. Model Performance & Sample Predictions
            try:
                if "models" in dataset_info and domain in dataset_info.get("models", {}):
                    model_data = dataset_info["models"][domain]
                    report["sections"]["model_performance"] = {
                        "model_type": model_data.get("model_type", "Unknown"),
                        "target_column": model_data.get("target_column", "Unknown"),
                        "metrics": model_data.get("metrics", {}),
                        "feature_count": len(model_data.get("feature_columns", [])),
                        "sample_predictions": model_data.get("sample_predictions", [])
                    }
            except Exception as e:
                report["sections"]["model_performance"] = {"error": f"Could not generate model performance: {str(e)}"}
            
            # 5. Feature Importance
            try:
                if "explanations" in dataset_info and domain in dataset_info.get("explanations", {}):
                    explanation = dataset_info["explanations"][domain]
                    report["sections"]["feature_importance"] = {
                        "top_features": dict(list(explanation.get("feature_importance", {}).items())[:10]),
                        "insights": explanation.get("human_readable_insights", [])
                    }
            except Exception as e:
                report["sections"]["feature_importance"] = {"error": f"Could not generate feature importance: {str(e)}"}
            
            # 6. Business Rules
            try:
                if "rules" in dataset_info and domain in dataset_info.get("rules", {}):
                    rules_data = dataset_info["rules"][domain]
                    report["sections"]["business_rules"] = {
                        "association_rules": rules_data.get("association_rules", [])[:10],
                        "if_then_rules": rules_data.get("if_then_rules", [])[:10],
                        "summary": rules_data.get("summary", {})
                    }
            except Exception as e:
                report["sections"]["business_rules"] = {"error": f"Could not generate business rules: {str(e)}"}
            
            # 7. Recommendations
            try:
                report["sections"]["recommendations"] = self._generate_recommendations(
                    dataset_info, domain
                )
            except Exception as e:
                report["sections"]["recommendations"] = [f"Could not generate recommendations: {str(e)}"]
            
            # 8. Visualization Suggestions
            try:
                report["sections"]["visualization_suggestions"] = self._generate_viz_suggestions(
                    dataset_info, domain
                )
            except Exception as e:
                report["sections"]["visualization_suggestions"] = [f"Could not generate visualization suggestions: {str(e)}"]
            
            # 9. Business-Friendly Summary (per requirements)
            try:
                formatter = BusinessFormatter()
                model_data = dataset_info.get("models", {}).get(domain, {})
                rules_data = dataset_info.get("rules", {}).get(domain, {})
                explain_data = dataset_info.get("explanations", {}).get(domain, {})
                
                # Get key rules
                all_rules = (rules_data.get("if_then_rules", []) + 
                            rules_data.get("association_rules", []))
                key_rules = formatter.highlight_key_rules(all_rules, max_rules=5)
                
                # Get relationships
                feature_impact = explain_data.get("feature_importance", {})
                relationships = formatter.get_relationships_explanation(feature_impact, domain)
                
                # Generate summary
                model_metrics = model_data.get("metrics", {})
                data_issues = []
                if dataset_info.get("preprocessed_data", {}).get(domain, {}).get("preprocessing_info", {}).get("missing_values_before", {}):
                    missing = dataset_info["preprocessed_data"][domain]["preprocessing_info"]["missing_values_before"]
                    total_missing = sum(missing.values())
                    if total_missing > 0:
                        data_issues.append(f"Dataset had {total_missing} missing values that were handled during processing.")
                
                summary = formatter.generate_summary(
                    domain, model_metrics, key_rules, relationships, data_issues
                )
                
                report["sections"]["business_summary"] = summary
            except Exception as e:
                report["sections"]["business_summary"] = {
                    "what_we_learned": ["Analysis completed successfully."],
                    "what_to_do_next": ["Review the results and apply insights to your business."],
                    "limitations": [f"Some summary information could not be generated: {str(e)}"]
                }
            
            return report
        except Exception as e:
            # Return a minimal report with error information
            return {
                "report_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "dataset_id": dataset_id,
                "domain": domain,
                "generated_at": datetime.now().isoformat(),
                "error": f"Error generating report: {str(e)}",
                "sections": {}
            }
    
    def _generate_dataset_summary(self, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dataset summary"""
        df = dataset_info["raw_data"]
        return {
            "filename": dataset_info.get("filename", "Unknown"),
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "upload_time": dataset_info.get("upload_time")
        }
    
    def _generate_recommendations(self, dataset_info: Dict[str, Any], domain: str) -> list:
        """Generate recommendations"""
        recommendations = []
        
        # Model performance recommendations
        if "models" in dataset_info and domain in dataset_info["models"]:
            metrics = dataset_info["models"][domain]["metrics"]
            
            if "accuracy" in metrics:
                if metrics["accuracy"] < 0.7:
                    recommendations.append(
                        "Model accuracy is below 70%. Consider feature engineering or trying different models."
                    )
                elif metrics["accuracy"] > 0.9:
                    recommendations.append(
                        "Model shows excellent accuracy. Consider validating on unseen data to check for overfitting."
                    )
            
            if "r2" in metrics:
                if metrics["r2"] < 0.5:
                    recommendations.append(
                        "R² score is low. The model may not capture all patterns. Consider adding more features."
                    )
        
        # Data quality recommendations
        df = dataset_info["raw_data"]
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
        if missing_pct > 0.1:
            recommendations.append(
                f"High percentage of missing values ({missing_pct:.1%}). Consider data collection improvements."
            )
        
        # Domain-specific recommendations
        if domain == "HR":
            recommendations.append(
                "For HR domain, consider tracking employee satisfaction surveys and performance reviews."
            )
        elif domain == "Finance":
            recommendations.append(
                "For Finance domain, consider implementing budget alerts based on extracted rules."
            )
        elif domain == "Sales":
            recommendations.append(
                "For Sales domain, use forecasting models to predict demand and optimize inventory."
            )
        
        return recommendations
    
    def _generate_viz_suggestions(self, dataset_info: Dict[str, Any], domain: str) -> list:
        """Generate visualization suggestions"""
        suggestions = []
        
        if "models" in dataset_info and domain in dataset_info["models"]:
            suggestions.append("Feature importance bar chart")
            suggestions.append("Model performance metrics dashboard")
        
        if "explanations" in dataset_info and domain in dataset_info["explanations"]:
            suggestions.append("SHAP summary plot")
            suggestions.append("LIME explanation plots for sample predictions")
        
        if "rules" in dataset_info and domain in dataset_info["rules"]:
            suggestions.append("Business rules network graph")
            suggestions.append("Association rules confidence vs support scatter plot")
        
        if domain == "Sales":
            suggestions.append("Time series forecast plot")
            suggestions.append("Sales trend analysis")
        
        if domain == "Finance":
            suggestions.append("Budget vs actual comparison chart")
            suggestions.append("Expense distribution histogram")
        
        if domain == "HR":
            suggestions.append("Attrition rate by department")
            suggestions.append("Employee satisfaction heatmap")
        
        return suggestions

