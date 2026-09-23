# Banking Transaction Anomaly Explanation Generator 🏦 AI Compliance Dashboard

An interactive, professional banking application built with **Python**, **Streamlit**, **Pandas**, and the **Gemini API**.

This tool inspects flagged banking transactions, visualizes key metrics and anomaly rule triggers, and leverages Gemini (`gemini-3.6-flash`) to generate human-readable explanations and actionable mitigation steps for compliance and fraud prevention officers.

---

## 📁 Repository Structure

```
.
├── app.py                  # Main Streamlit dashboard application
├── data/
│   └── transactions.json   # Synthetic banking transactions database
├── services/
│   └── explainer.py        # Gemini API integration service & prompt engine
├── requirements.txt        # Python package dependencies
├── .env.example            # Template for environment variables (GEMINI_API_KEY)
└── README.md               # Project documentation
```

---

## ⚡ Key Features

1. **Synthetic Transaction Ledger**: Realistically models fraud indicators including Impossible Geo-Velocity, TOR exit nodes, card testing micro-purchases, and rapid account draining.
2. **Interactive Risk Filtering**: Dynamic search by customer name, merchant, account ID, anomaly status, or risk score threshold.
3. **Deep Inspector View**: Side-by-side inspection of transaction metadata, historical 90-day average amount comparison, and device fingerprinting.
4. **AI Anomaly Explanation**: One-click generation of structured AI risk assessments via Gemini API (`gemini-3.6-flash`).
5. **Actionable Mitigation Guidance**: Outputs prioritized response steps (Immediate Lock, Out-of-band Verification, SAR Compliance filing).
6. **Graceful Fallback & Error Handling**: Includes demo mode and offline heuristic fallback if API key is not configured.

---

## 🚀 Quickstart Guide

### 1. Clone & Set Up Environment

```bash
# Navigate to project directory
cd Bank

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Gemini API Key

Copy `.env.example` to `.env` and set your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

*(Note: If no API key is provided, the application will run in Demo Mode using heuristic explanations).*

### 3. Run the Streamlit Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🛡️ Technologies Used

- **Python 3.10+**
- **Streamlit**: Web dashboard framework
- **Pandas**: Data manipulation and transaction table filtering
- **Gemini API (`google-genai`)**: Gemini inference engine (`gemini-3.6-flash`)
- **Python-Dotenv**: Environment configuration management
