import math
from numbers import Real
from typing import Any

import streamlit as st
import yfinance as yf

from chatbot import (
    ChatbotConfigurationError,
    FinancialChatbot,
    build_messages,
)

st.set_page_config(
    page_title="StockSage",
    page_icon=":chart_with_upwards_trend:",
    layout="centered",
)


def default_messages() -> list[dict[str, str]]:
    return [
        {
            "role": "assistant",
            "content": (
                "Hi, I am StockSage. Ask me about markets, investing concepts, "
                "portfolio strategy, or financial news you want to understand."
            ),
        }
    ]


def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = default_messages()


def is_missing(value: Any) -> bool:
    if value in (None, "", "N/A"):
        return True
    return isinstance(value, Real) and math.isnan(float(value))


def first_available(*values: Any) -> Any:
    for value in values:
        if not is_missing(value):
            return value
    return None


def format_price(value: Any, currency: str = "USD") -> str:
    if is_missing(value) or not isinstance(value, Real):
        return "N/A"
    return f"{currency} {float(value):,.2f}"


def format_market_cap(value: Any, currency: str = "USD") -> str:
    if is_missing(value) or not isinstance(value, Real):
        return "N/A"
    value = float(value)

    units = [
        (1_000_000_000_000, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
    ]

    for divisor, suffix in units:
        if abs(value) >= divisor:
            return f"{currency} {value / divisor:,.2f}{suffix}"

    return f"{currency} {value:,.0f}"


def format_ratio(value: Any) -> str:
    if is_missing(value) or not isinstance(value, Real):
        return "N/A"
    return f"{float(value):,.2f}"


@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker: str) -> dict[str, Any]:
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("Enter a ticker symbol.")

    stock = yf.Ticker(symbol)

    try:
        fast_info = dict(stock.fast_info)
    except Exception:
        fast_info = {}

    try:
        info = stock.info or {}
    except Exception:
        info = {}

    currency = first_available(info.get("currency"), fast_info.get("currency"), "USD")

    data = {
        "symbol": symbol,
        "name": first_available(info.get("longName"), info.get("shortName"), symbol),
        "currency": currency,
        "current_price": first_available(
            fast_info.get("last_price"),
            fast_info.get("lastPrice"),
            info.get("currentPrice"),
            info.get("regularMarketPrice"),
            info.get("previousClose"),
        ),
        "market_cap": first_available(
            fast_info.get("market_cap"),
            fast_info.get("marketCap"),
            info.get("marketCap"),
        ),
        "pe_ratio": first_available(info.get("trailingPE"), info.get("forwardPE")),
        "week_52_high": first_available(
            fast_info.get("year_high"),
            fast_info.get("yearHigh"),
            info.get("fiftyTwoWeekHigh"),
        ),
        "week_52_low": first_available(
            fast_info.get("year_low"),
            fast_info.get("yearLow"),
            info.get("fiftyTwoWeekLow"),
        ),
    }

    values = [
        data["current_price"],
        data["market_cap"],
        data["pe_ratio"],
        data["week_52_high"],
        data["week_52_low"],
    ]
    if all(value is None for value in values):
        raise ValueError(f"No market data found for `{symbol}`.")

    return data


def render_stock_panel() -> None:
    st.divider()
    st.markdown("**Market Data**")

    ticker = st.text_input(
        "Ticker",
        value=st.session_state.get("ticker", "AAPL"),
        max_chars=16,
        help="Enter a ticker symbol such as AAPL, MSFT, TSLA, or INFY.NS.",
    )
    # Ensure ticker is a string before calling strip() to satisfy type checkers
    st.session_state.ticker = (ticker or "").strip().upper()

    if not st.session_state.ticker:
        st.caption("Enter a ticker to view market data.")
        return

    try:
        data = fetch_stock_data(st.session_state.ticker)
    except Exception as exc:
        st.error(f"Could not load stock data: {exc}")
        return

    currency = data["currency"]
    st.caption(f"{data['name']} ({data['symbol']})")
    st.metric("Current Price", format_price(data["current_price"], currency))
    st.metric("Market Cap", format_market_cap(data["market_cap"], currency))
    st.metric("PE Ratio", format_ratio(data["pe_ratio"]))
    st.metric("52-Week High", format_price(data["week_52_high"], currency))
    st.metric("52-Week Low", format_price(data["week_52_low"], currency))


def render_sidebar() -> None:
    with st.sidebar:
        st.title("StockSage")
        st.caption("A financial education chatbot powered by Gemini 2.5 Flash.")

        st.divider()
        st.markdown("**Settings**")
        st.session_state.temperature = st.slider(
            "Response creativity",
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.get("temperature", 0.3)),
            step=0.1,
            help="Lower values are more focused. Higher values are more exploratory.",
        )

        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = default_messages()
            st.rerun()

        render_stock_panel()

        st.divider()
        st.info(
            "StockSage is for education only and does not provide personalized "
            "financial, tax, or legal advice."
        )


def render_header() -> None:
    st.title("StockSage")
    st.caption(
        "Ask clear financial questions. Get grounded, beginner-friendly answers."
    )


def render_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def main() -> None:
    initialize_state()
    render_sidebar()
    render_header()
    render_history()

    user_prompt = st.chat_input("Ask StockSage about stocks, ETFs, risk, valuation...")

    if not user_prompt:
        return

    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()

        try:
            chatbot = FinancialChatbot(
                temperature=float(st.session_state.get("temperature", 0.3))
            )
            messages = build_messages(st.session_state.messages)
            answer = chatbot.reply(messages)
        except ChatbotConfigurationError as exc:
            answer = (
                "I could not start the Gemini connection. "
                f"{exc}\n\nCheck your `.env` file and restart Streamlit."
            )
        except Exception as exc:
            answer = (
                "Something went wrong while generating a response. "
                "Please try again in a moment.\n\n"
                f"Technical detail: `{type(exc).__name__}: {exc}`"
            )

        response_placeholder.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
