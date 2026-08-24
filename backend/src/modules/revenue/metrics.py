from datetime import datetime, timezone
from typing import Dict, Any, List

# Exchange rates relative to INR (reporting currency)
EXCHANGE_RATES_TO_INR: Dict[str, float] = {
    "INR": 1.0,
    "USD": 83.5,
    "EUR": 90.2,
    "GBP": 105.8,
    "AUD": 54.6,
    "CAD": 61.2,
    "SGD": 62.1,
    "AED": 22.7,
}

METRIC_DICTIONARY = {
    "gross_revenue": "Amount attributed to sales before refunds, fees, or taxes, per the source's definition.",
    "refunds": "Total money returned or reversed to customers.",
    "fees": "Payment gateway processing fees and platform store cuts (e.g. Google/Apple commissions).",
    "taxes": "Collected value-added taxes, GST, or regional sales taxes.",
    "net_revenue": "Normalized dashboard net metric: Gross - Refunds - Fees - Taxes = Net Proceeds.",
    "mrr": "Monthly Recurring Revenue = Active recurring subscriptions multiplied by normalized monthly value.",
    "arr": "Annual Recurring Revenue = MRR * 12.",
    "churn_rate": "Percentage of subscription cancellations over the selected timeframe.",
    "arpu": "Average Revenue Per User = Total Net Revenue / Active Paying Users."
}


def convert_to_reporting_currency(amount: float, from_currency: str, reporting_currency: str = "INR") -> tuple[float, float]:
    """Convert foreign amount to reporting currency and return (converted_amount, exchange_rate)."""
    curr = (from_currency or "INR").upper()
    rate = EXCHANGE_RATES_TO_INR.get(curr, 1.0)
    converted = amount * rate
    return round(converted, 2), rate


def calculate_mrr(active_subscriptions: List[Dict[str, Any]]) -> float:
    """Calculate Monthly Recurring Revenue (MRR) across active subscription plans."""
    total_mrr = 0.0
    for sub in active_subscriptions:
        status = (sub.get("status") or "").lower()
        if status not in ["active", "trialing"]:
            continue

        amount = float(sub.get("amount") or sub.get("plan_amount") or 0.0)
        curr = (sub.get("currency") or "INR").upper()
        rate = EXCHANGE_RATES_TO_INR.get(curr, 1.0)
        inr_amount = amount * rate

        interval = (sub.get("interval") or sub.get("plan_interval") or "month").lower()
        if "year" in interval or "annual" in interval:
            total_mrr += (inr_amount / 12.0)
        elif "week" in interval:
            total_mrr += (inr_amount * 4.33)
        elif "day" in interval:
            total_mrr += (inr_amount * 30.0)
        else:
            # Default monthly
            total_mrr += inr_amount

    return round(total_mrr, 2)
