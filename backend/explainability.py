from typing import Dict, Any, List

class ExplainabilityEngine:
    """Provides model explainability using manual feature tracking - Pure Python"""
    
    def explain(self, model: Any, X_data: List[List[float]], y_data: List[Any],
                feature_columns: List[str], model_type: str) -> Dict[str, Any]:
        """Generate explanations using manual feature impact analysis"""
        explanation = {
            "feature_importance": {},
            "feature_impact_table": [],
            "human_readable_insights": []
        }
        
        # Extract feature importance from rules
        if isinstance(model, list):
            # Classification rules
            feature_importance = self._extract_importance_from_rules(model, feature_columns)
        elif isinstance(model, dict) and "weights" in model:
            # Regression rules (weights)
            feature_importance = self._extract_importance_from_weights(model, feature_columns)
        else:
            # Fallback: calculate correlation-based importance
            feature_importance = self._calculate_correlation_importance(
                X_data, y_data, feature_columns
            )
        
        explanation["feature_importance"] = feature_importance
        
        # Generate feature impact table
        explanation["feature_impact_table"] = self._generate_feature_impact_table(
            feature_importance
        )
        
        # Generate human-readable insights
        explanation["human_readable_insights"] = self._generate_insights(
            feature_importance, X_data, y_data, feature_columns, model_type
        )
        
        return explanation
    
    def _extract_importance_from_rules(self, rules: List[Dict[str, Any]],
                                      feature_columns: List[str]) -> Dict[str, float]:
        """Extract feature importance from classification rules"""
        feature_counts = {}
        feature_confidences = {}
        
        for rule in rules:
            feat_name = rule.get("feature", "")
            if feat_name in feature_columns:
                # Count how many times feature appears in rules
                feature_counts[feat_name] = feature_counts.get(feat_name, 0) + 1
                # Sum confidences
                confidence = rule.get("confidence", 0.5)
                feature_confidences[feat_name] = feature_confidences.get(feat_name, 0.0) + confidence
        
        # Calculate importance as weighted count
        importance_dict = {}
        total_weight = sum(feature_confidences.values())
        
        for feat_name in feature_columns:
            count = feature_counts.get(feat_name, 0)
            confidence_sum = feature_confidences.get(feat_name, 0.0)
            
            if total_weight > 0:
                importance = confidence_sum / total_weight
            else:
                importance = count / len(feature_columns) if feature_columns else 0.0
            
            importance_dict[feat_name] = importance
        
        # Normalize
        total = sum(importance_dict.values())
        if total > 0:
            importance_dict = {k: v / total for k, v in importance_dict.items()}
        
        return importance_dict
    
    def _extract_importance_from_weights(self, rules: Dict[str, Any],
                                        feature_columns: List[str]) -> Dict[str, float]:
        """Extract feature importance from regression weights"""
        weights = rules.get("weights", {})
        
        # Use absolute weights as importance
        importance_dict = {}
        abs_weights = {k: abs(v) for k, v in weights.items()}
        total = sum(abs_weights.values())
        
        for feat_name in feature_columns:
            if feat_name in abs_weights:
                importance_dict[feat_name] = abs_weights[feat_name] / total if total > 0 else 0.0
            else:
                importance_dict[feat_name] = 0.0
        
        # Normalize
        total_importance = sum(importance_dict.values())
        if total_importance > 0:
            importance_dict = {k: v / total_importance for k, v in importance_dict.items()}
        
        return importance_dict
    
    def _calculate_correlation_importance(self, X_data: List[List[float]], y_data: List[Any],
                                         feature_columns: List[str]) -> Dict[str, float]:
        """Calculate feature importance using correlation - Pure Python"""
        importance_dict = {}
        
        # Convert y_data to numeric if possible
        y_numeric = []
        for val in y_data:
            try:
                y_numeric.append(float(val))
            except:
                y_numeric.append(0.0)
        
        y_mean = sum(y_numeric) / len(y_numeric) if y_numeric else 0.0
        
        # Calculate correlation for each feature
        correlations = {}
        for feat_idx, feat_name in enumerate(feature_columns):
            feat_values = [x[feat_idx] for x in X_data]
            feat_mean = sum(feat_values) / len(feat_values) if feat_values else 0.0
            
            # Calculate correlation (covariance / (std_x * std_y))
            covariance = 0.0
            feat_variance = 0.0
            y_variance = 0.0
            
            for i in range(len(feat_values)):
                feat_diff = feat_values[i] - feat_mean
                y_diff = y_numeric[i] - y_mean
                covariance += feat_diff * y_diff
                feat_variance += feat_diff * feat_diff
                y_variance += y_diff * y_diff
            
            feat_std = (feat_variance / len(feat_values)) ** 0.5 if feat_values else 1.0
            y_std = (y_variance / len(y_numeric)) ** 0.5 if y_numeric else 1.0
            
            if feat_std > 0 and y_std > 0:
                correlation = (covariance / len(feat_values)) / (feat_std * y_std)
            else:
                correlation = 0.0
            
            correlations[feat_name] = abs(correlation)
        
        # Normalize correlations to get importance
        total_corr = sum(correlations.values())
        if total_corr > 0:
            importance_dict = {k: v / total_corr for k, v in correlations.items()}
        else:
            # Equal importance if no correlation
            importance_dict = {k: 1.0 / len(feature_columns) for k in feature_columns}
        
        return importance_dict
    
    def _generate_feature_impact_table(self, feature_importance: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate feature impact table with High/Medium/Low classification"""
        impact_table = []
        
        # Sort by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        # Determine thresholds
        if sorted_features:
            max_importance = sorted_features[0][1] if sorted_features else 0.0
            high_threshold = max_importance * 0.7
            medium_threshold = max_importance * 0.3
            
            for feature, importance in sorted_features:
                if importance >= high_threshold:
                    impact_level = "High"
                elif importance >= medium_threshold:
                    impact_level = "Medium"
                else:
                    impact_level = "Low"
                
                impact_table.append({
                    "feature": feature,
                    "importance": float(importance),
                    "impact": impact_level
                })
        
        return impact_table
    
    def _generate_insights(self, feature_importance: Dict[str, float],
                          X_data: List[List[float]], y_data: List[Any],
                          feature_columns: List[str], model_type: str) -> List[str]:
        """Generate human-readable insights - Pure Python"""
        insights = []
        
        # Top features
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_features = [feat[0] for feat in sorted_features[:5]]
        
        insights.append(f"Top 5 most important features: {', '.join(top_features)}")
        
        # Feature impact analysis
        for feat_name in top_features[:3]:
            if feat_name in feature_columns:
                feat_idx = feature_columns.index(feat_name)
                feat_values = [x[feat_idx] for x in X_data]
                
                if feat_values:
                    # Calculate statistics
                    feat_mean = sum(feat_values) / len(feat_values)
                    sorted_vals = sorted(feat_values)
                    median_val = sorted_vals[len(sorted_vals) // 2]
                    
                    if model_type.endswith("classifier"):
                        # For classification, show distribution
                        insights.append(
                            f"{feat_name} has high impact. "
                            f"Average value: {feat_mean:.2f}, Median: {median_val:.2f}"
                        )
                    else:
                        # For regression, show correlation
                        insights.append(
                            f"{feat_name} significantly influences predictions. "
                            f"Average value: {feat_mean:.2f}"
                        )
        
        # Key insight
        if top_features:
            top_feature = top_features[0]
            insights.append(
                f"Key insight: {top_feature} has the highest impact on predictions. "
                f"Focus on this feature for better predictions."
            )
        
        return insights
