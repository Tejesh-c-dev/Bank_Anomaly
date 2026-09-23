import os
import json
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

from google import genai

# Load environment variables from .env if present
load_dotenv()

def get_gemini_client():
    """
    Initialize and return the Gemini client if GEMINI_API_KEY is available.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "your_gemini_api_key_here":
        return None, "Gemini API key not configured. Please set GEMINI_API_KEY in your .env file or environment."

    try:
        client = genai.Client(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"Failed to initialize Gemini client: {str(e)}"


def _parse_response(response: Any) -> Dict[str, Any]:
    content = getattr(response, "text", None)
    if not content or not content.strip():
        raise ValueError("Gemini returned an empty response.")

    content = content.strip()
    if content.startswith("```json") and content.endswith("```"):
        content = content[7:-3].strip()
    elif content.startswith("```") and content.endswith("```"):
        content = content[3:-3].strip()

    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini returned JSON in an unexpected format.")

    summary = parsed.get("summary")
    reasons = parsed.get("reasons")
    actions = parsed.get("recommended_actions")
    if (
        not isinstance(summary, str)
        or not isinstance(reasons, list)
        or not isinstance(actions, list)
        or not all(isinstance(item, str) for item in reasons + actions)
    ):
        raise ValueError("Gemini returned JSON with an invalid explanation shape.")

    return {
        "summary": summary,
        "reasons": reasons,
        "recommended_actions": actions,
    }


def generate_explanation(
    transaction: Dict[str, Any],
    model_name: str = "llama-3.3-70b-versatile",
) -> Dict[str, Any]:
    """Generate a grounded, customer-friendly explanation for a transaction.

    The function always returns the documented response shape, including when
    the API is unavailable or the model returns malformed JSON.
    """
    empty_result = {
        "summary": "An explanation is currently unavailable.",
        "reasons": [],
        "recommended_actions": [
            "Review the transaction details in your banking app.",
            "Contact your bank through an official channel if you do not recognize it.",
        ],
    }

    client, error_msg = get_gemini_client()
    if client is None:
        return {
            **empty_result,
            "summary": error_msg or empty_result["summary"],
        }

    system_prompt = """You explain flagged bank transactions to customers.
Use only the supplied verified transaction facts. Never invent or infer transaction details.
Never claim that a transaction is definitely fraud; describe it as flagged or potentially unusual.
Clearly explain why it was flagged, using only supplied facts.
Use simple, customer-friendly language.
Provide 2-3 practical recommended actions.

Return only valid JSON with exactly this shape:
{
  "summary": "",
  "reasons": [],
  "recommended_actions": []
}
The summary must be a string. Reasons and recommended_actions must be arrays of strings.
"""
    user_prompt = (
        "Explain this transaction using only the following verified structured information:\n"
        + json.dumps(transaction, ensure_ascii=True, sort_keys=True)
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt + "\n\n" + user_prompt,
        )
        try:
            return _parse_response(response)
        except (TypeError, ValueError, json.JSONDecodeError) as parse_error:
            response_text = getattr(response, "text", None)
            if response_text and response_text.strip():
                return {
                    **empty_result,
                    "summary": response_text.strip(),
                }
            raise parse_error
    except Exception as e:
        return {
            **empty_result,
            "summary": f"Gemini API error: {str(e)}",
        }


def generate_anomaly_explanation(transaction: Dict[str, Any], model_name: str = "llama-3.3-70b-versatile") -> Tuple[str, bool]:
    """
    Sends the selected transaction metadata to Gemini to generate an explicit,
    expert banking anomaly explanation and recommended action plan.

    Returns:
        Tuple[str, bool]: (markdown_content, is_error)
    """
    client, error_msg = get_gemini_client()

    # Fallback response if API key is not configured
    if not client:
        customer_id_or_name = transaction.get('customer_name') or transaction.get('customer_id', 'Unknown Customer')
        risk_score_val = transaction.get('anomaly_score') if 'anomaly_score' in transaction else transaction.get('risk_score', 0.0)
        avg_amt_val = transaction.get('historical_avg_amount') if 'historical_avg_amount' in transaction else transaction.get('average_transaction_amount', 0.0)
        reasons_list = transaction.get('rule_flags') or transaction.get('reasons') or ['None']

        fallback_markdown = f"""
> ⚠️ **Gemini API Key Notice**: {error_msg}
> *Showing standard rule-based heuristic explanation below for demonstration.*

---

### 🚨 Risk Summary
Transaction **{transaction.get('transaction_id')}** for **{customer_id_or_name}** has been flagged with an anomaly score of **{risk_score_val * 100:.0f}%**.

### 🔍 Why It Was Flagged
- **Amount Deviation**: ${transaction.get('amount', 0):,.2f} USD vs historical average of ${avg_amt_val:,.2f} USD ({((transaction.get('amount', 0) / max(avg_amt_val, 1)) - 1)*100:.0f}% higher).
- **Location Mismatch**: Transaction originated from **{transaction.get('location')}** while customer's usual location is **{transaction.get('usual_location')}**.
- **Device Anomaly**: Executed via **{transaction.get('device_info')}** (Usual device: *{transaction.get('usual_device')}*).
- **Rule Triggers**: {', '.join(reasons_list)}.

### 🧠 System Assessment (Rule Heuristic)
This transaction displays classic indicators of account compromise or high-risk unauthorized remote usage. The velocity and geographical gap between the registered cardholder residence and transaction point of origin suggest stolen credentials or device emulation.

### 🛡️ Recommended Actions
1. **Immediate Card Lock**: Temporarily freeze card linked to Account **{transaction.get('account_id', transaction.get('customer_id'))}**.
2. **Customer Contact**: Send urgent SMS / Push notification to verify purchase intent.
3. **Escalate to Fraud Desk**: Assign ticket to Tier-2 Fraud Prevention Operations.
        """
        return fallback_markdown, False

    # Construct rich context prompt for Gemini
    system_prompt = """You are a Lead Financial Fraud & Compliance Analyst at a Tier-1 International Investment & Commercial Bank.
Your role is to analyze flagged banking transactions and provide crisp, professional, authoritative risk explanations and actionable next steps for bank operators and compliance officers.

Formulate your response in clean, beautifully structured Markdown using the exact section headers below:

### 📑 Executive Summary
Provide a 2-sentence executive summary of the risk level and core concern.

### 🔍 Why It Was Flagged
List bullet points citing specific evidence from the transaction data (amount vs 90-day average, geo-location discrepancy, device/IP signatures, rule triggers).

### 🧠 In-Depth AI Risk Explanation
Provide an analytical breakdown explaining the probable attack vector or threat pattern (e.g. Account Takeover, Stolen Card Details, Card Testing Bot, Impossible Travel Velocity, Offshore Money Laundering).

### 🛡️ Recommended Actions
Categorize actions clearly:
- **Immediate Mitigation** (e.g. Card Freeze, Wire Hold)
- **Customer Verification** (e.g. Out-of-band 2FA call, SMS challenge)
- **Compliance & Operations** (e.g. SAR Filing, Account Lock, False Positive review)
"""

    user_prompt = f"""Please analyze the following banking transaction data and generate a comprehensive fraud analysis:

Transaction Data:
{json.dumps(transaction, indent=2)}

Ensure all numbers, amounts, locations, and device details from the JSON are explicitly referenced in your analysis.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt + "\n\n" + user_prompt,
        )
        explanation = getattr(response, "text", None)
        if not explanation or not explanation.strip():
            raise ValueError("Gemini returned an empty response.")
        return explanation, False
    except Exception as e:
        return f"⚠️ **Gemini API Error**: {str(e)}", True
