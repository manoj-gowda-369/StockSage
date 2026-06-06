# StockSage

StockSage is a simple Streamlit financial chatbot powered by the Google Gemini API. It keeps chat history in the Streamlit session, provides a clean chat UI, and handles missing configuration or API failures gracefully.

## Features

- Financial education chatbot
- Google Gemini 2.5 Flash API integration
- Stock market data from yfinance
- Session-based chat history
- Clean Streamlit chat interface
- Configurable response creativity
- Friendly error handling

## Project Structure

```text
StockSage/
|-- app.py
|-- chatbot.py
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create your environment file:

```bash
copy .env.example .env
```

4. Add your Gemini API key to `.env`:

```text
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## Run

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in your terminal.

## Notes

StockSage is for educational use only. It does not provide personalized financial, tax, or legal advice. Always verify important investment decisions with a qualified professional.
