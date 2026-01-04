# Automatic Mode Guide

## Overview

The **Automatic Mode** is designed for users who want a fully automated analysis workflow. Simply upload your dataset and the system will handle everything automatically.

## How It Works

When you select **Automatic Mode** and upload a dataset, the system will:

1. ✅ **Upload & Parse** - Upload and parse your dataset
2. ✅ **Detect Domain** - Automatically identify if it's HR, Finance, Sales, or Operations
3. ✅ **Preprocess** - Clean data, handle missing values, encode categories
4. ✅ **Select Target** - Intelligently select the best column to predict
5. ✅ **Train Model** - Train appropriate model based on domain
6. ✅ **Explain** - Generate SHAP/LIME explanations
7. ✅ **Extract Rules** - Extract business rules using Apriori
8. ✅ **Generate Report** - Create comprehensive report

## Target Column Selection

The system automatically selects the best target column based on:

- **Domain-specific keywords**: 
  - HR: attrition, leave, turnover, performance
  - Finance: budget, expense, cost, revenue
  - Sales: sales, revenue, quantity, demand
  - Operations: efficiency, throughput, capacity

- **Data characteristics**: Falls back to last column or first numeric column if no domain match

## What You Get

After automatic processing, you'll see:

1. **Domain Detection Results** - Detected domains with confidence scores
2. **Model Performance** - Accuracy, RMSE, R², F1 score (depending on model type)
3. **Feature Importance** - Top 10 features influencing predictions
4. **Human-Readable Insights** - Easy-to-understand explanations
5. **Business Rules** - Association rules and if-then rules with confidence/lift
6. **Recommendations** - Actionable suggestions based on analysis
7. **Visualization Suggestions** - Recommended charts and dashboards

## When to Use Automatic Mode

✅ **Use Automatic Mode when:**
- You want quick results
- You're not sure which column to predict
- You trust the system's domain detection
- You want a complete analysis in one go

❌ **Use Manual Mode when:**
- You need to select a specific target column
- You want to adjust preprocessing parameters
- You need to customize model training
- You want to review each step before proceeding

## Example Workflow

1. Open application → Select **🤖 Automatic Mode**
2. Click upload area → Select your CSV file
3. Watch progress steps update in real-time
4. Review complete results when processing finishes

That's it! No manual steps required.

## Troubleshooting

**If automatic mode fails:**
- Check that your dataset has at least 50 rows
- Ensure at least one column is suitable for prediction
- Try manual mode for more control
- Check browser console (F12) for error messages

**If target column selection is wrong:**
- Use manual mode to select your preferred column
- Rename your target column to include domain keywords (e.g., "attrition", "sales", "expense")

