from typing import Dict, Any, List, Tuple

class ModelTrainer:
    """Trains rule-based prediction models - Pure Python"""
    
    def train(self, df, domain: str, target_column: str) -> Dict[str, Any]:
        """Train rule-based model for domain"""
        # Prepare features and target
        feature_columns = [col for col in df.columns if col != target_column]
        
        if not feature_columns:
            raise ValueError("No feature columns available")
        
        # Get data as lists
        X_data = []
        y_data = []
        for idx in range(len(df)):
            row_features = []
            for col in feature_columns:
                val = df.iloc[idx][col]
                # Convert to numeric if possible
                try:
                    row_features.append(float(val))
                except:
                    row_features.append(0.0)
            X_data.append(row_features)
            
            target_val = df.iloc[idx][target_column]
            y_data.append(target_val)
        
        # Determine if classification or regression
        is_classification = self._is_classification(y_data)
        
        # Split data (80/20)
        split_idx = int(len(X_data) * 0.8)
        X_train = X_data[:split_idx]
        y_train = y_data[:split_idx]
        X_test = X_data[split_idx:]
        y_test = y_data[split_idx:]
        
        # Train rule-based model
        if is_classification:
            model_result = self._train_classification_rules(
                X_train, y_train, X_test, y_test, feature_columns, domain
            )
        else:
            model_result = self._train_regression_rules(
                X_train, y_train, X_test, y_test, feature_columns, domain
            )
        
        return model_result
    
    def _is_classification(self, y: List[Any]) -> bool:
        """Determine if target is classification or regression"""
        # Count unique values
        unique_values = {}
        for val in y:
            val_str = str(val)
            unique_values[val_str] = unique_values.get(val_str, 0) + 1
        
        unique_ratio = len(unique_values) / len(y) if y else 0
        
        # If few unique values relative to dataset size, likely classification
        return unique_ratio < 0.1 or len(unique_values) <= 10
    
    def _train_classification_rules(self, X_train: List[List[float]], y_train: List[Any],
                                   X_test: List[List[float]], y_test: List[Any],
                                   feature_columns: List[str], domain: str) -> Dict[str, Any]:
        """Train rule-based classification model"""
        # Build rules based on thresholds
        rules = self._build_classification_rules(X_train, y_train, feature_columns)
        
        # Make predictions
        y_pred = []
        for x in X_test:
            pred = self._predict_with_rules(x, rules, feature_columns)
            y_pred.append(pred)
        
        # Calculate metrics
        metrics = self._calculate_classification_metrics(y_test, y_pred)
        
        # Generate sample predictions
        sample_predictions = self._generate_sample_predictions(
            X_test, y_test, y_pred, is_classification=True
        )
        
        return {
            "model": rules,  # Store rules instead of model object
            "model_type": "rule_based_classifier",
            "metrics": metrics,
            "feature_columns": feature_columns,
            "sample_predictions": sample_predictions,
            "rules": rules
        }
    
    def _train_regression_rules(self, X_train: List[List[float]], y_train: List[Any],
                                X_test: List[List[float]], y_test: List[Any],
                                feature_columns: List[str], domain: str) -> Dict[str, Any]:
        """Train rule-based regression model"""
        # Convert y_train to numeric
        y_train_numeric = []
        for val in y_train:
            try:
                y_train_numeric.append(float(val))
            except:
                y_train_numeric.append(0.0)
        
        # Build regression rules (weighted average based on feature values)
        rules = self._build_regression_rules(X_train, y_train_numeric, feature_columns)
        
        # Make predictions
        y_pred = []
        for x in X_test:
            pred = self._predict_regression(x, rules, feature_columns)
            y_pred.append(pred)
        
        # Convert y_test to numeric
        y_test_numeric = []
        for val in y_test:
            try:
                y_test_numeric.append(float(val))
            except:
                y_test_numeric.append(0.0)
        
        # Calculate metrics
        metrics = self._calculate_regression_metrics(y_test_numeric, y_pred)
        
        # Generate sample predictions
        sample_predictions = self._generate_sample_predictions(
            X_test, y_test_numeric, y_pred, is_classification=False
        )
        
        return {
            "model": rules,
            "model_type": "rule_based_regressor",
            "metrics": metrics,
            "feature_columns": feature_columns,
            "sample_predictions": sample_predictions,
            "rules": rules
        }
    
    def _build_classification_rules(self, X_train: List[List[float]], y_train: List[Any],
                                   feature_columns: List[str]) -> List[Dict[str, Any]]:
        """Build classification rules using thresholds"""
        rules = []
        
        # For each feature, find thresholds that best separate classes
        for feat_idx, feat_name in enumerate(feature_columns):
            # Get feature values
            feat_values = [x[feat_idx] for x in X_train]
            
            # Get unique classes
            classes = {}
            for val in y_train:
                val_str = str(val)
                classes[val_str] = classes.get(val_str, 0) + 1
            
            # Find thresholds
            if len(feat_values) > 0:
                sorted_values = sorted(feat_values)
                # Use quartiles as thresholds
                n = len(sorted_values)
                thresholds = [
                    sorted_values[n//4],
                    sorted_values[n//2],
                    sorted_values[3*n//4]
                ]
                
                for threshold in thresholds:
                    # Count class distribution above/below threshold
                    above_classes = {}
                    below_classes = {}
                    
                    for i, val in enumerate(feat_values):
                        class_val = str(y_train[i])
                        if val >= threshold:
                            above_classes[class_val] = above_classes.get(class_val, 0) + 1
                        else:
                            below_classes[class_val] = below_classes.get(class_val, 0) + 1
                    
                    # Find dominant class for each region
                    if above_classes:
                        above_class = max(above_classes.items(), key=lambda x: x[1])[0]
                        rules.append({
                            "feature": feat_name,
                            "threshold": threshold,
                            "condition": ">=",
                            "prediction": above_class,
                            "confidence": above_classes[above_class] / sum(above_classes.values())
                        })
                    
                    if below_classes:
                        below_class = max(below_classes.items(), key=lambda x: x[1])[0]
                        rules.append({
                            "feature": feat_name,
                            "threshold": threshold,
                            "condition": "<",
                            "prediction": below_class,
                            "confidence": below_classes[below_class] / sum(below_classes.values())
                        })
        
        return rules
    
    def _build_regression_rules(self, X_train: List[List[float]], y_train: List[float],
                               feature_columns: List[str]) -> Dict[str, Any]:
        """Build regression rules (feature weights)"""
        # Calculate correlation-like weights for each feature
        weights = {}
        feature_means = {}
        target_mean = sum(y_train) / len(y_train) if y_train else 0.0
        
        for feat_idx, feat_name in enumerate(feature_columns):
            feat_values = [x[feat_idx] for x in X_train]
            feat_mean = sum(feat_values) / len(feat_values) if feat_values else 0.0
            feature_means[feat_name] = feat_mean
            
            # Calculate simple correlation (covariance / variance)
            covariance = 0.0
            feat_variance = 0.0
            
            for i in range(len(feat_values)):
                feat_diff = feat_values[i] - feat_mean
                target_diff = y_train[i] - target_mean
                covariance += feat_diff * target_diff
                feat_variance += feat_diff * feat_diff
            
            if feat_variance > 0:
                weight = covariance / feat_variance
            else:
                weight = 0.0
            
            weights[feat_name] = weight
        
        return {
            "weights": weights,
            "feature_means": feature_means,
            "target_mean": target_mean
        }
    
    def _predict_with_rules(self, x: List[float], rules: List[Dict[str, Any]],
                           feature_columns: List[str]) -> Any:
        """Predict using classification rules"""
        # Count votes from matching rules
        votes = {}
        for rule in rules:
            feat_name = rule["feature"]
            if feat_name in feature_columns:
                feat_idx = feature_columns.index(feat_name)
                feat_val = x[feat_idx]
                threshold = rule["threshold"]
                condition = rule["condition"]
                
                matches = False
                if condition == ">=" and feat_val >= threshold:
                    matches = True
                elif condition == "<" and feat_val < threshold:
                    matches = True
                
                if matches:
                    pred = rule["prediction"]
                    confidence = rule.get("confidence", 0.5)
                    votes[pred] = votes.get(pred, 0) + confidence
        
        if votes:
            # Return class with highest votes
            return max(votes.items(), key=lambda x: x[1])[0]
        else:
            # Default: return most common class from training
            return "Unknown"
    
    def _predict_regression(self, x: List[float], rules: Dict[str, Any],
                           feature_columns: List[str]) -> float:
        """Predict using regression rules"""
        weights = rules["weights"]
        feature_means = rules["feature_means"]
        target_mean = rules["target_mean"]
        
        prediction = target_mean
        
        for feat_idx, feat_name in enumerate(feature_columns):
            if feat_name in weights:
                feat_val = x[feat_idx]
                feat_mean = feature_means.get(feat_name, 0.0)
                weight = weights[feat_name]
                
                # Add weighted contribution
                prediction += weight * (feat_val - feat_mean)
        
        return prediction
    
    def _calculate_classification_metrics(self, y_true: List[Any], y_pred: List[Any]) -> Dict[str, float]:
        """Calculate classification metrics - Pure Python"""
        if not y_true or not y_pred:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}
        
        # Accuracy
        correct = 0
        for i in range(len(y_true)):
            if str(y_true[i]) == str(y_pred[i]):
                correct += 1
        accuracy = correct / len(y_true) if y_true else 0.0
        
        # Precision, Recall, F1 (simplified)
        true_positives = {}
        false_positives = {}
        false_negatives = {}
        
        for i in range(len(y_true)):
            true_class = str(y_true[i])
            pred_class = str(y_pred[i])
            
            if true_class == pred_class:
                true_positives[true_class] = true_positives.get(true_class, 0) + 1
            else:
                false_positives[pred_class] = false_positives.get(pred_class, 0) + 1
                false_negatives[true_class] = false_negatives.get(true_class, 0) + 1
        
        # Calculate weighted precision/recall
        precision_sum = 0.0
        recall_sum = 0.0
        total = len(y_true)
        
        all_classes = set([str(v) for v in y_true] + [str(v) for v in y_pred])
        for cls in all_classes:
            tp = true_positives.get(cls, 0)
            fp = false_positives.get(cls, 0)
            fn = false_negatives.get(cls, 0)
            
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            
            class_count = sum(1 for v in y_true if str(v) == cls)
            weight = class_count / total if total > 0 else 0.0
            
            precision_sum += prec * weight
            recall_sum += rec * weight
        
        precision = precision_sum
        recall = recall_sum
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }
    
    def _calculate_regression_metrics(self, y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
        """Calculate regression metrics - Pure Python"""
        if not y_true or not y_pred:
            return {"rmse": 0.0, "mae": 0.0, "r2": 0.0}
        
        n = len(y_true)
        
        # MAE
        mae = sum(abs(y_true[i] - y_pred[i]) for i in range(n)) / n if n > 0 else 0.0
        
        # RMSE
        mse = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n)) / n if n > 0 else 0.0
        rmse = mse ** 0.5
        
        # R²
        y_mean = sum(y_true) / n if n > 0 else 0.0
        ss_tot = sum((y_true[i] - y_mean) ** 2 for i in range(n))
        ss_res = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n))
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            "rmse": rmse,
            "mae": mae,
            "r2": r2
        }
    
    def _generate_sample_predictions(self, X_test: List[List[float]], y_test: List[Any],
                                    y_pred: List[Any], is_classification: bool) -> List[Dict[str, Any]]:
        """Generate sample predictions"""
        sample_predictions = []
        n_samples = min(5, len(X_test))
        
        for i in range(n_samples):
            actual = y_test[i]
            predicted = y_pred[i]
            
            # Determine if correct
            if is_classification:
                correct = str(actual) == str(predicted)
            else:
                # For regression, consider correct if within 10% error
                try:
                    actual_float = float(actual)
                    pred_float = float(predicted)
                    error_pct = abs(actual_float - pred_float) / abs(actual_float) if actual_float != 0 else 0.0
                    correct = error_pct <= 0.1
                except:
                    correct = False
            
            sample_predictions.append({
                "index": i,
                "actual": actual,
                "predicted": predicted,
                "correct": correct
            })
        
        return sample_predictions
