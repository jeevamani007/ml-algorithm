from typing import List, Dict, Any

class DomainDetector:
    """Detects domain(s) of a dataset based on column names and data types - Pure Python.

    NOTE: Public consumers of this class should treat the supported domains as:
    HR, Finance, Sales, Education, General.
    Any internal / legacy domains will be mapped into this set.
    """
    
    # Domain-specific keywords (internal)
    DOMAIN_KEYWORDS = {
        "HR": [
            "employee", "emp", "staff", "worker", "attrition", "leave", "absence",
            "department", "manager", "salary", "performance", "rating", "tenure",
            "experience", "age", "gender", "marital", "education", "training",
            "promotion", "satisfaction", "overtime", "work_life", "bonus", "deduction"
        ],
        "Finance": [
            "budget", "expense", "cost", "revenue", "income", "profit", "loss",
            "financial", "account", "transaction", "payment", "invoice", "amount",
            "price", "fee", "charge", "investment", "asset", "liability", "equity",
            "cash", "balance", "forecast", "quarter", "fiscal"
        ],
        "Sales": [
            "sales", "revenue", "order", "customer", "client", "product", "item",
            "quantity", "price", "discount", "commission", "territory", "region",
            "demand", "forecast", "target", "quota", "pipeline", "opportunity",
            "conversion", "lead", "deal", "contract", "subscription"
        ],
        # Operations will be mapped to General in the public output
        "Operations": [
            "operation", "process", "efficiency", "throughput", "capacity", "utilization",
            "inventory", "stock", "supply", "demand", "warehouse", "logistics",
            "delivery", "shipping", "production", "manufacturing", "quality", "defect",
            "maintenance", "downtime", "cycle_time", "lead_time"
        ],
        # Education domain support (mapped to "Education" in public results)
        "Education": [
            "student", "pupil", "learner", "rollno", "roll_no", "admission",
            "grade", "class", "section", "semester", "course", "subject",
            "attendance", "marks", "score", "gpa", "cgpa", "exam", "test",
            "assignment", "teacher", "faculty", "department", "batch"
        ],
    }
    
    def detect_domains(self, df) -> List[Dict[str, Any]]:
        """Detect domain(s) from dataset columns - Pure Python"""
        # Get columns as list
        columns = list(df.columns)
        columns_lower = [col.lower() for col in columns]
        domain_scores = {}
        
        # Score each domain based on keyword matches
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = 0
            matched_columns = []
            
            for keyword in keywords:
                for col in columns_lower:
                    if keyword in col:
                        score += 1
                        # Get original column name
                        original_col = columns[columns_lower.index(col)]
                        if original_col not in matched_columns:
                            matched_columns.append(original_col)
            
            if score > 0:
                domain_scores[domain] = {
                    "score": score,
                    "matched_columns": matched_columns,
                    "confidence": min(score / len(keywords), 1.0)
                }
        
        # Sort by score
        sorted_domains = sorted(
            domain_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )
        
        # Get row count using pure Python
        row_count = len(df)
        
        # Helper to map internal domain names to the public, constrained set
        def _public_domain_name(internal_domain: str) -> str:
            if internal_domain in ("HR", "Finance", "Sales", "Education"):
                return internal_domain
            # Any other internal domains are surfaced as General
            return "General"
        
        # Format results (using only the allowed public domain labels)
        detected_domains = []
        for internal_domain, info in sorted_domains:
            public_domain = _public_domain_name(internal_domain)
            detected_domains.append({
                "domain": public_domain,
                "confidence": round(info["confidence"], 3),
                "score": info["score"],
                "matched_columns": info["matched_columns"],
                "data_types": self._get_domain_data_types(df, info["matched_columns"]),
                "row_count": row_count
            })
        
        # If no domain detected, classify as "General"
        if not detected_domains:
            detected_domains.append({
                "domain": "General",
                "confidence": 0.5,
                "score": 0,
                "matched_columns": columns,
                "data_types": self._get_domain_data_types(df, columns),
                "row_count": row_count
            })
        
        return detected_domains
    
    def _get_domain_data_types(self, df, columns: List[str]) -> Dict[str, str]:
        """Get data types for matched columns - Pure Python"""
        dtypes = {}
        for col in columns:
            if col in df.columns:
                # Get sample value to determine type
                sample_val = None
                for idx in range(min(10, len(df))):
                    val = df.iloc[idx][col]
                    if val is not None:
                        sample_val = val
                        break
                
                if sample_val is not None:
                    if isinstance(sample_val, (int, float)):
                        dtypes[col] = "numeric"
                    else:
                        dtypes[col] = "categorical"
                else:
                    dtypes[col] = "unknown"
        return dtypes
