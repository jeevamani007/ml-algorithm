from typing import Tuple, Dict, Any, List

class DataPreprocessor:
    """Handles data cleaning and preprocessing for different domains - Pure Python"""
    
    def preprocess(self, df, domain: str) -> Tuple[Any, Dict[str, Any]]:
        """Preprocess data based on domain - Pure Python"""
        preprocessing_info = {
            "original_shape": (len(df), len(df.columns)),
            "missing_values_before": self._count_missing(df),
            "operations": []
        }
        
        df_processed = df.copy()
        
        # 1. Handle missing values
        df_processed, missing_info = self._handle_missing_values(df_processed, domain)
        preprocessing_info["operations"].append(missing_info)
        preprocessing_info["missing_values_after"] = self._count_missing(df_processed)
        
        # 2. Encode categorical variables using pure Python
        df_processed, encoding_info = self._encode_categorical(df_processed)
        preprocessing_info["operations"].append(encoding_info)
        
        # 3. Handle outliers (optional, domain-specific)
        if domain in ["Finance", "Sales"]:
            df_processed, outlier_info = self._handle_outliers(df_processed)
            preprocessing_info["operations"].append(outlier_info)
        
        # 4. Normalize/Scale if needed (pure Python)
        df_processed, scaling_info = self._normalize_data(df_processed, domain)
        preprocessing_info["operations"].append(scaling_info)

        # 5. Silent feature engineering (domain-aware, formulas not exposed)
        df_processed, fe_info = self._feature_engineering(df_processed, domain)
        preprocessing_info["operations"].append(fe_info)
        
        preprocessing_info["final_shape"] = (len(df_processed), len(df_processed.columns))
        preprocessing_info["columns"] = list(df_processed.columns)
        
        return df_processed, preprocessing_info
    
    def _count_missing(self, df) -> Dict[str, int]:
        """Count missing values per column - Pure Python"""
        missing = {}
        for col in df.columns:
            count = 0
            for idx in range(len(df)):
                val = df.iloc[idx][col]
                if val is None or (isinstance(val, float) and str(val) == 'nan'):
                    count += 1
            missing[col] = count
        return missing
    
    def _handle_missing_values(self, df, domain: str) -> Tuple[Any, Dict[str, Any]]:
        """Handle missing values based on domain - Pure Python"""
        info = {"operation": "missing_values", "strategy": {}}
        
        for col in df.columns:
            missing_count = 0
            for idx in range(len(df)):
                val = df.iloc[idx][col]
                if val is None or (isinstance(val, float) and str(val) == 'nan'):
                    missing_count += 1
            
            if missing_count > 0:
                missing_pct = missing_count / len(df)
                
                if missing_pct > 0.5:
                    # Drop column if more than 50% missing
                    df = df.drop(columns=[col])
                    info["strategy"][col] = f"dropped ({missing_pct:.1%} missing)"
                else:
                    # Determine if numeric or categorical
                    is_numeric = self._is_numeric_column(df, col)
                    
                    if is_numeric:
                        # Fill with median
                        median_val = self._calculate_median(df, col)
                        for idx in range(len(df)):
                            val = df.iloc[idx][col]
                            if val is None or (isinstance(val, float) and str(val) == 'nan'):
                                df.iloc[idx, df.columns.get_loc(col)] = median_val
                        info["strategy"][col] = f"filled with median ({median_val:.2f})"
                    else:
                        # Fill with mode
                        mode_val = self._calculate_mode(df, col)
                        for idx in range(len(df)):
                            val = df.iloc[idx][col]
                            if val is None or (isinstance(val, float) and str(val) == 'nan'):
                                df.iloc[idx, df.columns.get_loc(col)] = mode_val
                        info["strategy"][col] = f"filled with mode ({mode_val})"
        
        return df, info
    
    def _is_numeric_column(self, df, col: str) -> bool:
        """Check if column is numeric - Pure Python"""
        for idx in range(min(10, len(df))):
            val = df.iloc[idx][col]
            if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                return isinstance(val, (int, float))
        return False
    
    def _calculate_median(self, df, col: str) -> float:
        """Calculate median - Pure Python"""
        values = []
        for idx in range(len(df)):
            val = df.iloc[idx][col]
            if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                try:
                    values.append(float(val))
                except:
                    pass
        
        if not values:
            return 0.0
        
        values.sort()
        n = len(values)
        if n % 2 == 0:
            return (values[n//2 - 1] + values[n//2]) / 2.0
        else:
            return values[n//2]
    
    def _calculate_mode(self, df, col: str) -> Any:
        """Calculate mode - Pure Python"""
        value_counts = {}
        for idx in range(len(df)):
            val = df.iloc[idx][col]
            if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                val_str = str(val)
                value_counts[val_str] = value_counts.get(val_str, 0) + 1
        
        if not value_counts:
            return "Unknown"
        
        mode_val = max(value_counts.items(), key=lambda x: x[1])[0]
        # Try to return original type
        for idx in range(len(df)):
            val = df.iloc[idx][col]
            if val is not None and str(val) == mode_val:
                return val
        return mode_val
    
    def _encode_categorical(self, df) -> Tuple[Any, Dict[str, Any]]:
        """Encode categorical variables using pure Python dictionaries"""
        info = {"operation": "categorical_encoding", "encoded_columns": {}}
        
        for col in df.columns:
            # Check if categorical (not numeric)
            if not self._is_numeric_column(df, col):
                # Create encoding dictionary
                unique_values = []
                for idx in range(len(df)):
                    val = df.iloc[idx][col]
                    if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                        val_str = str(val)
                        if val_str not in unique_values:
                            unique_values.append(val_str)
                
                # Create mapping: value -> integer
                encoding_map = {val: idx for idx, val in enumerate(unique_values)}
                
                # Apply encoding
                for idx in range(len(df)):
                    val = df.iloc[idx][col]
                    if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                        encoded_val = encoding_map.get(str(val), 0)
                        df.iloc[idx, df.columns.get_loc(col)] = encoded_val
                    else:
                        df.iloc[idx, df.columns.get_loc(col)] = 0
                
                info["encoded_columns"][col] = {
                    "method": "label_encoding",
                    "unique_values": len(unique_values),
                    "mapping": encoding_map
                }
        
        return df, info
    
    def _handle_outliers(self, df, method: str = "iqr") -> Tuple[Any, Dict[str, Any]]:
        """Handle outliers using IQR method - Pure Python"""
        info = {"operation": "outlier_handling", "outliers_handled": {}}
        
        numeric_cols = [col for col in df.columns if self._is_numeric_column(df, col)]
        
        for col in numeric_cols:
            values = []
            for idx in range(len(df)):
                val = df.iloc[idx][col]
                if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                    try:
                        values.append(float(val))
                    except:
                        pass
            
            if len(values) < 4:
                continue
            
            values.sort()
            n = len(values)
            q1_idx = n // 4
            q3_idx = 3 * n // 4
            Q1 = values[q1_idx]
            Q3 = values[q3_idx]
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = 0
            for idx in range(len(df)):
                val = df.iloc[idx][col]
                if val is not None:
                    try:
                        val_float = float(val)
                        if val_float < lower_bound or val_float > upper_bound:
                            # Cap outlier
                            if val_float < lower_bound:
                                df.iloc[idx, df.columns.get_loc(col)] = lower_bound
                            else:
                                df.iloc[idx, df.columns.get_loc(col)] = upper_bound
                            outliers += 1
                    except:
                        pass
            
            if outliers > 0:
                info["outliers_handled"][col] = {
                    "count": outliers,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound
                }
        
        return df, info
    
    def _normalize_data(self, df, domain: str) -> Tuple[Any, Dict[str, Any]]:
        """Normalize data if needed - Pure Python (min-max scaling)"""
        info = {"operation": "normalization", "normalized_columns": []}
        
        # Only normalize if domain requires it
        if domain in ["Finance", "Sales", "Operations"]:
            numeric_cols = [col for col in df.columns if self._is_numeric_column(df, col)]
            
            for col in numeric_cols:
                values = []
                for idx in range(len(df)):
                    val = df.iloc[idx][col]
                    if val is not None and not (isinstance(val, float) and str(val) == 'nan'):
                        try:
                            values.append(float(val))
                        except:
                            pass
                
                if not values:
                    continue
                
                min_val = min(values)
                max_val = max(values)
                
                if max_val - min_val > 0:
                    # Min-max normalization: (x - min) / (max - min)
                    for idx in range(len(df)):
                        val = df.iloc[idx][col]
                        if val is not None:
                            try:
                                normalized = (float(val) - min_val) / (max_val - min_val)
                                df.iloc[idx, df.columns.get_loc(col)] = normalized
                            except:
                                pass
                    
                    info["normalized_columns"].append(col)
                    info["method"] = "min_max_scaling"
        
        return df, info

    def _feature_engineering(self, df, domain: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Create additional, business-friendly metrics silently.

        The goal is to enrich the dataset with derived signals such as:
        - Attendance percentage
        - Salary per month / per year
        - Experience in years
        - Simple calendar features for trend analysis (month / year)

        Formulas are intentionally not exposed to the outside world; only the
        presence of engineered features is recorded in the metadata.
        """
        info: Dict[str, Any] = {
            "operation": "feature_engineering",
            "engineered_features": [],
            "domain": domain
        }

        # 1. Attendance-related features
        try:
            cols_lower = {col.lower(): col for col in df.columns}
            present_candidates = [c for c in df.columns if "present" in c.lower()]
            total_candidates = [c for c in df.columns if "total" in c.lower() or "working_days" in c.lower()]

            if present_candidates and total_candidates:
                present_col = present_candidates[0]
                total_col = total_candidates[0]
                new_col = "attendance_percentage"
                try:
                    # Use vectorized operations when possible
                    df[new_col] = (df[present_col].astype("float64") / df[total_col].astype("float64")).clip(lower=0, upper=1) * 100.0
                    info["engineered_features"].append(new_col)
                except Exception:
                    # Fall back to row-wise safe computation
                    values = []
                    for idx in range(len(df)):
                        try:
                            pres = float(df.iloc[idx][present_col])
                            tot = float(df.iloc[idx][total_col])
                            if tot > 0:
                                values.append(max(0.0, min(100.0, (pres / tot) * 100.0)))
                            else:
                                values.append(0.0)
                        except Exception:
                            values.append(0.0)
                    df[new_col] = values
                    info["engineered_features"].append(new_col)
        except Exception:
            # Best-effort only – failures here should never break preprocessing
            pass

        # 2. Salary per month / year (HR / Finance heavy)
        try:
            salary_cols = [c for c in df.columns if "salary" in c.lower() or "ctc" in c.lower() or "compensation" in c.lower()]
            for col in salary_cols:
                name_lower = col.lower()
                if "annual" in name_lower or "year" in name_lower:
                    new_col = f"{col}_per_month"
                    try:
                        df[new_col] = (df[col].astype("float64") / 12.0)
                        info["engineered_features"].append(new_col)
                    except Exception:
                        continue
                elif "month" in name_lower or "monthly" in name_lower:
                    new_col = f"{col}_per_year"
                    try:
                        df[new_col] = (df[col].astype("float64") * 12.0)
                        info["engineered_features"].append(new_col)
                    except Exception:
                        continue
        except Exception:
            pass

        # 3. Experience in years (HR / General)
        try:
            exp_cols = [c for c in df.columns if "experience" in c.lower() or "tenure" in c.lower() or "years_in_company" in c.lower()]
            for col in exp_cols:
                name_lower = col.lower()
                if "month" in name_lower:
                    new_col = f"{col}_years"
                    try:
                        df[new_col] = (df[col].astype("float64") / 12.0)
                        info["engineered_features"].append(new_col)
                    except Exception:
                        continue
        except Exception:
            pass

        # 4. Calendar / trend features from date-like columns
        try:
            import pandas as pd  # Local import to avoid hard dependency elsewhere

            date_cols = [c for c in df.columns if "date" in c.lower() or "timestamp" in c.lower()]
            for col in date_cols:
                try:
                    dt_series = pd.to_datetime(df[col], errors="coerce")
                    if dt_series.notna().any():
                        month_col = f"{col}_month"
                        year_col = f"{col}_year"
                        df[month_col] = dt_series.dt.month
                        df[year_col] = dt_series.dt.year
                        info["engineered_features"].extend([month_col, year_col])
                except Exception:
                    continue
        except Exception:
            pass

        return df, info
