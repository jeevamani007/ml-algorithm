from typing import Dict, Any, List
import re

class ColumnAnalyzer:
    """Analyzes columns and generates user-friendly purpose explanations"""
    
    # Column purpose patterns
    COLUMN_PATTERNS = {
        # HR Domain
        "employee_id": {
            "purpose": "Unique identifier for each employee in the system",
            "category": "Identifier",
            "examples": ["employee_id", "emp_id", "id", "employee_number"]
        },
        "name": {
            "purpose": "Employee's full name or identifier",
            "category": "Personal Information",
            "examples": ["name", "employee_name", "full_name", "emp_name"]
        },
        "age": {
            "purpose": "Employee's age in years - used to analyze age-related patterns and risk factors",
            "category": "Demographics",
            "examples": ["age", "employee_age"]
        },
        "salary": {
            "purpose": "Employee's salary or compensation amount - helps identify salary trends and fairness",
            "category": "Compensation",
            "examples": ["salary", "compensation", "pay", "wage", "income"]
        },
        "department": {
            "purpose": "Department or division where the employee works - used for department-wise analysis",
            "category": "Organizational",
            "examples": ["department", "dept", "division", "unit"]
        },
        "attendance": {
            "purpose": "Employee attendance percentage or count - key indicator of engagement and risk",
            "category": "Performance",
            "examples": ["attendance", "attendance_percentage", "attendance_rate", "present_days"]
        },
        "leave_count": {
            "purpose": "Number of leave days taken - high values may indicate risk of attrition",
            "category": "Leave Management",
            "examples": ["leave_count", "leaves", "leave_days", "absent_days", "days_off"]
        },
        "attrition": {
            "purpose": "Whether employee left the company (Yes/No) - the main target for prediction",
            "category": "Outcome",
            "examples": ["attrition", "left", "resigned", "turnover", "churn"]
        },
        
        # Finance Domain
        "expense": {
            "purpose": "Expense amount or cost incurred - helps track spending patterns and budget overruns",
            "category": "Cost",
            "examples": ["expense", "cost", "expenditure", "spending"]
        },
        "revenue": {
            "purpose": "Revenue or income generated - used to analyze profitability and growth",
            "category": "Income",
            "examples": ["revenue", "income", "sales_revenue", "earnings"]
        },
        "budget": {
            "purpose": "Budgeted amount allocated - compared with actual to identify variances",
            "category": "Planning",
            "examples": ["budget", "budgeted_amount", "allocated", "planned"]
        },
        "profit": {
            "purpose": "Profit or net income - indicates financial performance",
            "category": "Performance",
            "examples": ["profit", "net_profit", "net_income", "earnings"]
        },
        
        # Sales Domain
        "sales": {
            "purpose": "Sales amount or quantity - primary metric for sales performance",
            "category": "Sales Metric",
            "examples": ["sales", "sales_amount", "sales_volume", "revenue"]
        },
        "quantity": {
            "purpose": "Quantity of items sold - helps analyze sales volume patterns",
            "category": "Volume",
            "examples": ["quantity", "qty", "units_sold", "volume"]
        },
        "order": {
            "purpose": "Order number or order details - tracks individual transactions",
            "category": "Transaction",
            "examples": ["order", "order_id", "order_number", "transaction"]
        },
        "customer": {
            "purpose": "Customer identifier or name - used for customer segmentation analysis",
            "category": "Customer",
            "examples": ["customer", "customer_id", "client", "customer_name"]
        },
        
        # General
        "date": {
            "purpose": "Date or timestamp - used for time-series analysis and trend identification",
            "category": "Temporal",
            "examples": ["date", "timestamp", "time", "created_date", "transaction_date"]
        },
        "month": {
            "purpose": "Month of the year - helps analyze seasonal patterns and monthly trends",
            "category": "Temporal",
            "examples": ["month", "month_name", "period"]
        },
        "year": {
            "purpose": "Year value - used for year-over-year comparisons and long-term trends",
            "category": "Temporal",
            "examples": ["year", "fiscal_year", "year_value"]
        }
    }
    
    def analyze_columns(self, df, domain: str = None) -> Dict[str, Any]:
        """Analyze all columns and generate purpose explanations"""
        column_analyses = {}
        
        for col in df.columns:
            analysis = self._analyze_single_column(df, col, domain)
            column_analyses[col] = analysis
        
        return {
            "columns": column_analyses,
            "total_columns": len(df.columns),
            "domain": domain or "General"
        }
    
    def _analyze_single_column(self, df, col_name: str, domain: str = None) -> Dict[str, Any]:
        """Analyze a single column and generate purpose"""
        col_lower = col_name.lower().strip()
        
        # Try to match known patterns
        matched_pattern = None
        for pattern_name, pattern_info in self.COLUMN_PATTERNS.items():
            for example in pattern_info["examples"]:
                if example in col_lower or col_lower in example:
                    matched_pattern = pattern_info
                    break
            if matched_pattern:
                break
        
        # Get data type and statistics
        data_type, stats = self._get_column_stats(df, col_name)
        
        # Generate purpose if matched
        if matched_pattern:
            purpose = matched_pattern["purpose"]
            category = matched_pattern["category"]
        else:
            # Generate generic purpose based on data type and name
            purpose = self._generate_generic_purpose(col_name, data_type, stats)
            category = self._infer_category(col_name, data_type)
        
        # Generate business context
        business_context = self._generate_business_context(col_name, data_type, stats, domain)
        
        return {
            "column_name": col_name,
            "purpose": purpose,
            "category": category,
            "data_type": data_type,
            "statistics": stats,
            "business_context": business_context,
            "usage_in_analysis": self._suggest_usage(col_name, data_type, domain)
        }
    
    def _get_column_stats(self, df, col_name: str) -> tuple:
        """Get column statistics"""
        values = []
        for idx in range(len(df)):
            val = df.iloc[idx][col_name]
            if val is not None and str(val) != 'nan':
                values.append(val)
        
        if not values:
            return "empty", {}
        
        # Determine type
        numeric_count = 0
        for val in values[:100]:  # Sample first 100
            try:
                float(val)
                numeric_count += 1
            except:
                pass
        
        is_numeric = numeric_count / min(len(values), 100) > 0.8
        
        stats = {
            "total_values": len(values),
            "unique_values": len(set(str(v) for v in values)),
            "missing_count": len(df) - len(values)
        }
        
        if is_numeric:
            numeric_vals = []
            for val in values:
                try:
                    numeric_vals.append(float(val))
                except:
                    pass
            
            if numeric_vals:
                sorted_vals = sorted(numeric_vals)
                stats.update({
                    "min": sorted_vals[0],
                    "max": sorted_vals[-1],
                    "mean": sum(numeric_vals) / len(numeric_vals),
                    "median": sorted_vals[len(sorted_vals) // 2] if sorted_vals else 0
                })
            return "numeric", stats
        else:
            # Categorical stats
            value_counts = {}
            for val in values:
                val_str = str(val)
                value_counts[val_str] = value_counts.get(val_str, 0) + 1
            
            top_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["top_values"] = top_values
            return "categorical", stats
    
    def _generate_generic_purpose(self, col_name: str, data_type: str, stats: Dict[str, Any]) -> str:
        """Generate generic purpose based on column name and type"""
        col_lower = col_name.lower()
        
        # Check for common keywords
        if "id" in col_lower or "identifier" in col_lower:
            return f"Unique identifier for records - used to uniquely identify each row in the dataset"
        
        if "count" in col_lower or "number" in col_lower:
            return f"Count or number value - represents quantity or frequency of occurrences"
        
        if "percentage" in col_lower or "rate" in col_lower or "%" in col_name:
            return f"Percentage or rate value - represents a proportion or ratio"
        
        if "date" in col_lower or "time" in col_lower:
            return f"Date or time information - used for temporal analysis and trend identification"
        
        if data_type == "numeric":
            if stats.get("mean", 0) > 1000:
                return f"Large numeric value - likely represents monetary amounts, quantities, or measurements"
            else:
                return f"Numeric value - represents a measurable quantity or score"
        else:
            return f"Categorical value - represents a category, label, or classification"
    
    def _infer_category(self, col_name: str, data_type: str) -> str:
        """Infer category from column name"""
        col_lower = col_name.lower()
        
        if "id" in col_lower:
            return "Identifier"
        elif "name" in col_lower:
            return "Personal Information"
        elif "date" in col_lower or "time" in col_lower:
            return "Temporal"
        elif "amount" in col_lower or "price" in col_lower or "cost" in col_lower:
            return "Financial"
        elif data_type == "numeric":
            return "Numeric Metric"
        else:
            return "Categorical"
    
    def _generate_business_context(self, col_name: str, data_type: str, stats: Dict[str, Any], domain: str = None) -> str:
        """Generate business context for the column"""
        col_lower = col_name.lower()
        
        context_parts = []
        
        # Domain-specific context
        if domain == "HR":
            if "attendance" in col_lower or "leave" in col_lower:
                context_parts.append("This metric is crucial for identifying employees at risk of attrition.")
            if "salary" in col_lower or "compensation" in col_lower:
                context_parts.append("Helps analyze compensation fairness and retention factors.")
        
        elif domain == "Finance":
            if "expense" in col_lower or "cost" in col_lower:
                context_parts.append("Key metric for budget control and cost management.")
            if "revenue" in col_lower or "profit" in col_lower:
                context_parts.append("Essential for profitability analysis and financial planning.")
        
        elif domain == "Sales":
            if "sales" in col_lower or "revenue" in col_lower:
                context_parts.append("Primary metric for sales performance evaluation.")
            if "quantity" in col_lower:
                context_parts.append("Helps identify sales volume patterns and demand trends.")
        
        # Statistical context
        if data_type == "numeric" and stats.get("mean"):
            mean_val = stats["mean"]
            if mean_val > 0:
                context_parts.append(f"Average value is {mean_val:.2f}, which helps establish baseline expectations.")
        
        if stats.get("unique_values", 0) < 10:
            context_parts.append(f"Has {stats['unique_values']} unique values, making it suitable for categorical analysis.")
        
        return " ".join(context_parts) if context_parts else "This column contributes to overall data analysis and pattern detection."
    
    def _suggest_usage(self, col_name: str, data_type: str, domain: str = None) -> str:
        """Suggest how this column can be used in analysis"""
        col_lower = col_name.lower()
        
        usages = []
        
        # Check if it's an ID column
        if "id" in col_lower or "identifier" in col_lower:
            return "Use as a unique identifier. Not recommended as a prediction target."
        
        # Check if suitable as target
        if data_type == "numeric":
            if domain == "HR" and ("attrition" in col_lower or "risk" in col_lower):
                usages.append("Good candidate for prediction target")
            elif domain == "Finance" and ("profit" in col_lower or "loss" in col_lower):
                usages.append("Suitable for financial forecasting")
            elif domain == "Sales" and ("sales" in col_lower or "revenue" in col_lower):
                usages.append("Ideal for sales prediction")
            else:
                usages.append("Can be used as a feature or target variable")
        else:
            usages.append("Use as a categorical feature for pattern analysis")
        
        # Feature engineering suggestions
        if "date" in col_lower:
            usages.append("Can extract month, year, day-of-week for time-series analysis")
        
        if data_type == "numeric":
            usages.append("Can create bins (Low/Medium/High) for rule extraction")
        
        return ". ".join(usages) + "."

