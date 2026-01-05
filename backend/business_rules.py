from typing import Dict, Any, List

class BusinessRulesExtractor:
    """Extracts business rules using threshold and frequency analysis - Pure Python"""
    
    def extract_rules(self, df, domain: str, target_column: str = None,
                     min_support: float = 0.1, min_confidence: float = 0.5) -> Dict[str, Any]:
        """Extract business rules from data using pure Python"""
        rules = {
            "association_rules": [],
            "if_then_rules": [],
            "summary": {}
        }
        
        # 1. Association rules using frequency analysis
        try:
            association_rules_list = self._extract_association_rules(
                df, min_support, min_confidence
            )
            rules["association_rules"] = association_rules_list
        except Exception as e:
            rules["association_rules"] = [{"error": f"Association rules extraction failed: {str(e)}"}]
        
        # 2. If-Then rules from data patterns
        if_then_rules = self._extract_if_then_rules(df, domain, target_column)
        rules["if_then_rules"] = if_then_rules
        
        # 3. Summary
        rules["summary"] = {
            "total_association_rules": len([r for r in rules["association_rules"] if "error" not in r]),
            "total_if_then_rules": len(if_then_rules),
            "domain": domain
        }
        
        return rules
    
    def _extract_association_rules(self, df, min_support: float, min_confidence: float) -> List[Dict[str, Any]]:
        """Extract association rules using frequency analysis - Pure Python"""
        rules_list = []
        
        try:
            # Discretize numeric columns
            df_discretized = self._discretize_data(df)
            
            # Get all column-value pairs
            all_items = []
            for col in df_discretized.columns:
                unique_vals = {}
                for idx in range(len(df_discretized)):
                    val = df_discretized.iloc[idx][col]
                    if val is not None and str(val) != 'nan':
                        val_str = f"{col}={val}"
                        unique_vals[val_str] = unique_vals.get(val_str, 0) + 1
                all_items.extend(unique_vals.keys())
            
            # Calculate support for each item
            item_support = {}
            total_rows = len(df_discretized)
            
            for item in all_items:
                count = 0
                col_name = item.split('=')[0]
                item_val = '='.join(item.split('=')[1:])
                
                for idx in range(len(df_discretized)):
                    val = df_discretized.iloc[idx][col_name]
                    if val is not None and str(val) == item_val:
                        count += 1
                
                support = count / total_rows if total_rows > 0 else 0.0
                if support >= min_support:
                    item_support[item] = support
            
            # Generate rules: IF item1 THEN item2
            for item1 in item_support.keys():
                for item2 in item_support.keys():
                    if item1 != item2:
                        # Calculate support for both items together
                        col1 = item1.split('=')[0]
                        val1 = '='.join(item1.split('=')[1:])
                        col2 = item2.split('=')[0]
                        val2 = '='.join(item2.split('=')[1:])
                        
                        # Count co-occurrence
                        cooccurrence = 0
                        for idx in range(len(df_discretized)):
                            val_col1 = df_discretized.iloc[idx][col1]
                            val_col2 = df_discretized.iloc[idx][col2]
                            
                            if (val_col1 is not None and str(val_col1) == val1 and
                                val_col2 is not None and str(val_col2) == val2):
                                cooccurrence += 1
                        
                        support_both = cooccurrence / total_rows if total_rows > 0 else 0.0
                        support_item1 = item_support[item1]
                        
                        # Calculate confidence
                        confidence = support_both / support_item1 if support_item1 > 0 else 0.0
                        
                        # Calculate lift
                        support_item2 = item_support[item2]
                        lift = confidence / support_item2 if support_item2 > 0 else 0.0
                        
                        if confidence >= min_confidence and support_both >= min_support:
                            # Format rule in user-friendly way
                            rule_str = self._format_rule_string(item1, item2)
                            rules_list.append({
                                "rule": rule_str,
                                "support": support_both,
                                "confidence": confidence,
                                "lift": lift,
                                "antecedent": [item1],
                                "consequent": [item2],
                                "rule_type": "association"
                            })
            
            # Sort by confidence
            rules_list.sort(key=lambda x: x['confidence'], reverse=True)
        
        except Exception as e:
            return [{"error": f"Association rules extraction error: {str(e)}"}]
        
        return rules_list[:20]  # Return top 20 rules
    
    def _discretize_data(self, df) -> Any:
        """Discretize numeric columns into bins - Pure Python"""
        df_discretized = df.copy()
        
        for col in df.columns:
            # Check if numeric
            is_numeric = False
            values = []
            for idx in range(len(df)):
                val = df.iloc[idx][col]
                if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                    try:
                        float_val = float(val)
                        values.append(float_val)
                        is_numeric = True
                    except:
                        pass
            
            if is_numeric and len(values) > 0:
                # Discretize into quartiles
                sorted_values = sorted(values)
                n = len(sorted_values)
                
                if n >= 4:
                    q1_idx = n // 4
                    q2_idx = n // 2
                    q3_idx = 3 * n // 4
                    
                    q1 = sorted_values[q1_idx]
                    q2 = sorted_values[q2_idx]
                    q3 = sorted_values[q3_idx]
                    
                    # Apply discretization
                    for idx in range(len(df)):
                        val = df.iloc[idx][col]
                        if val is not None:
                            try:
                                val_float = float(val)
                                if val_float < q1:
                                    df_discretized.iloc[idx, df_discretized.columns.get_loc(col)] = "Low"
                                elif val_float < q2:
                                    df_discretized.iloc[idx, df_discretized.columns.get_loc(col)] = "Medium"
                                elif val_float < q3:
                                    df_discretized.iloc[idx, df_discretized.columns.get_loc(col)] = "High"
                                else:
                                    df_discretized.iloc[idx, df_discretized.columns.get_loc(col)] = "VeryHigh"
                            except:
                                pass
        
        return df_discretized
    
    def _format_rule_string(self, item1: str, item2: str) -> str:
        """Format rule string to be more user-readable"""
        # Extract column and value from item strings (format: "column=value")
        def parse_item(item_str):
            if '=' in item_str:
                parts = item_str.split('=', 1)
                return parts[0].strip(), parts[1].strip()
            return item_str, None
        
        col1, val1 = parse_item(item1)
        col2, val2 = parse_item(item2)
        
        # Format in user-friendly way
        # Example: "IF Leave Count = High THEN Attrition = High"
        if val1 and val2:
            return f"IF {col1} = {val1} THEN {col2} = {val2}"
        elif val1:
            return f"IF {col1} = {val1} THEN {col2}"
        elif val2:
            return f"IF {col1} THEN {col2} = {val2}"
        else:
            return f"IF {col1} THEN {col2}"
    
    def _format_if_then_rule(self, col: str, threshold: float, target_col: str, target_val: float, operator: str) -> str:
        """Format if-then rule in user-friendly way"""
        # Convert numeric values to categories for better readability
        col_lower = col.lower()
        target_lower = target_col.lower()
        
        # Format threshold based on column type
        if 'age' in col_lower:
            threshold_str = f"{threshold:.0f}"
        elif 'count' in col_lower or 'leave' in col_lower:
            threshold_str = f"{threshold:.0f}"
        else:
            threshold_str = f"{threshold:.2f}"
        
        # Format target value
        if 'attrition' in target_lower or 'risk' in target_lower:
            if target_val > 0.7:
                target_str = "High"
            elif target_val > 0.4:
                target_str = "Medium"
            else:
                target_str = "Low"
            return f"IF {col} {operator} {threshold_str} THEN {target_col} = {target_str}"
        else:
            return f"IF {col} {operator} {threshold_str} THEN {target_col} = {target_val:.2f}"
    
    def _extract_if_then_rules(self, df, domain: str, target_column: str = None) -> List[Dict[str, Any]]:
        """Extract if-then rules from data patterns - Pure Python"""
        rules = []
        
        if target_column and target_column in df.columns:
            # Get numeric columns
            numeric_cols = []
            for col in df.columns:
                if col != target_column:
                    # Check if numeric
                    is_numeric = False
                    for idx in range(min(10, len(df))):
                        val = df.iloc[idx][col]
                        if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                            try:
                                float(val)
                                is_numeric = True
                                break
                            except:
                                pass
                    
                    if is_numeric:
                        numeric_cols.append(col)
            
            # Extract rules for top 10 features
            for col in numeric_cols[:10]:
                try:
                    # Calculate thresholds
                    values = []
                    for idx in range(len(df)):
                        val = df.iloc[idx][col]
                        if val is not None:
                            try:
                                values.append(float(val))
                            except:
                                pass
                    
                    if len(values) < 4:
                        continue
                    
                    sorted_vals = sorted(values)
                    n = len(sorted_vals)
                    q25 = sorted_vals[n // 4]
                    median_val = sorted_vals[n // 2]
                    q75 = sorted_vals[3 * n // 4]
                    
                    # Get target values
                    target_values = []
                    for idx in range(len(df)):
                        val = df.iloc[idx][target_column]
                        if val is not None:
                            try:
                                target_values.append(float(val))
                            except:
                                pass
                    
                    if not target_values:
                        continue
                    
                    overall_avg = sum(target_values) / len(target_values)
                    
                    # Rule 1: Low values
                    low_count = 0
                    low_target_sum = 0.0
                    for idx in range(len(df)):
                        val = df.iloc[idx][col]
                        if val is not None:
                            try:
                                if float(val) < q25:
                                    low_count += 1
                                    target_val = df.iloc[idx][target_column]
                                    if target_val is not None:
                                        try:
                                            low_target_sum += float(target_val)
                                        except:
                                            pass
                            except:
                                pass
                    
                    if low_count > 0:
                        avg_target = low_target_sum / low_count
                        if abs(avg_target - overall_avg) > 0.1 * abs(overall_avg) if overall_avg != 0 else True:
                            # Format rule in user-friendly way
                            rule_str = self._format_if_then_rule(col, q25, target_column, avg_target, "<")
                            rules.append({
                                "rule": rule_str,
                                "support": low_count / len(df) if len(df) > 0 else 0.0,
                                "confidence": low_count / len(df) if len(df) > 0 else 0.0,
                                "lift": avg_target / overall_avg if overall_avg != 0 else 1.0,
                                "impact": "high" if abs(avg_target - overall_avg) > 0.2 * abs(overall_avg) else "medium"
                            })
                    
                    # Rule 2: High values
                    high_count = 0
                    high_target_sum = 0.0
                    for idx in range(len(df)):
                        val = df.iloc[idx][col]
                        if val is not None:
                            try:
                                if float(val) > q75:
                                    high_count += 1
                                    target_val = df.iloc[idx][target_column]
                                    if target_val is not None:
                                        try:
                                            high_target_sum += float(target_val)
                                        except:
                                            pass
                            except:
                                pass
                    
                    if high_count > 0:
                        avg_target = high_target_sum / high_count
                        if abs(avg_target - overall_avg) > 0.1 * abs(overall_avg) if overall_avg != 0 else True:
                            # Format rule in user-friendly way
                            rule_str = self._format_if_then_rule(col, q75, target_column, avg_target, ">")
                            rules.append({
                                "rule": rule_str,
                                "support": high_count / len(df) if len(df) > 0 else 0.0,
                                "confidence": high_count / len(df) if len(df) > 0 else 0.0,
                                "lift": avg_target / overall_avg if overall_avg != 0 else 1.0,
                                "impact": "high" if abs(avg_target - overall_avg) > 0.2 * abs(overall_avg) else "medium"
                            })
                
                except Exception as e:
                    continue
        
        # Domain-specific rules
        domain_rules = self._get_domain_specific_rules(df, domain)
        rules.extend(domain_rules)
        
        return rules[:15]  # Return top 15 rules
    
    def _get_domain_specific_rules(self, df, domain: str) -> List[Dict[str, Any]]:
        """Generate domain-specific business rules - Pure Python"""
        rules = []
        
        if domain == "HR":
            # Look for age/tenure patterns
            for col in df.columns:
                col_lower = col.lower()
                if 'age' in col_lower or 'tenure' in col_lower:
                    values = []
                    for idx in range(len(df)):
                        val = df.iloc[idx][col]
                        if val is not None:
                            try:
                                values.append(float(val))
                            except:
                                pass
                    
                    if len(values) >= 4:
                        sorted_vals = sorted(values)
                        threshold = sorted_vals[len(sorted_vals) // 4]
                        rules.append({
                            "rule": f"IF {col} < {threshold:.1f} THEN higher risk category",
                            "confidence": 0.7,
                            "impact": "medium"
                        })
        
        elif domain == "Finance":
            # Look for expense/budget patterns
            for col in df.columns:
                col_lower = col.lower()
                if 'expense' in col_lower or 'cost' in col_lower:
                    values = []
                    for idx in range(len(df)):
                        val = df.iloc[idx][col]
                        if val is not None:
                            try:
                                values.append(float(val))
                            except:
                                pass
                    
                    if len(values) >= 4:
                        sorted_vals = sorted(values)
                        threshold = sorted_vals[3 * len(sorted_vals) // 4]
                        rules.append({
                            "rule": f"IF {col} > {threshold:.2f} THEN budget alert",
                            "confidence": 0.6,
                            "impact": "high"
                        })
        
        elif domain == "Sales":
            # Look for sales patterns
            for col in df.columns:
                col_lower = col.lower()
                if 'quantity' in col_lower or 'order' in col_lower:
                    values = []
                    for idx in range(len(df)):
                        val = df.iloc[idx][col]
                        if val is not None:
                            try:
                                values.append(float(val))
                            except:
                                pass
                    
                    if len(values) >= 4:
                        sorted_vals = sorted(values)
                        threshold = sorted_vals[len(sorted_vals) // 2]
                        rules.append({
                            "rule": f"IF {col} > {threshold:.1f} THEN higher sales potential",
                            "confidence": 0.65,
                            "impact": "medium"
                        })
        
        return rules
