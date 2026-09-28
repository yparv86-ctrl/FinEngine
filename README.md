# 📊 FinEngine: Enterprise Valuation Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_APP_URL_HERE)

FinEngine is an institutional-grade equity valuation platform that automatically routes financial data into the appropriate pricing model based on sector architecture. Built for resilience and speed, it features in-memory caching, local database auditing, and dynamic sensitivity analysis.

## Core Architecture

* **Traffic-Cop Routing:** Automatically identifies financial institutions (banks, credit firms) and routes them to a Dividend Discount Model (DDM), while standard corporate entities default to a 3-Stage Discounted Cash Flow (DCF) model.
* **Valuation Multiverse:** Generates dynamic 2D sensitivity matrices cross-analyzing Cost of Capital/Equity against Terminal Growth/Dividend Growth.
* **Persistent Audit Ledger:** All valuations are logged into a local SQLite database (`valuations_history.db`) for cross-session tracking, with CSV export capabilities.
* **Financial Health Tracking:** Plots historical revenue/FCF and operating efficiency trendlines (FCF Margin, Net Margin, ROIC) to contextualize the intrinsic value.
* **Data Pipeline:** Leverages `yfinance` for ingestion, featuring custom alias mapping for messy SEC filings and automated imputation for missing line items.

## Tech Stack
* **Frontend/Hosting:** Streamlit, Streamlit Community Cloud
* **Data & Math:** Pandas, NumPy, yfinance
* **Database:** SQLite
* **Deliverables:** ReportLab (PDF Generation), Matplotlib

## Local Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/FinEngine.git](https://github.com/YOUR_USERNAME/FinEngine.git)
   cd FinEngine