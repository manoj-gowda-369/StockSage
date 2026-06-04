import streamlit as st

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

        st.divider()
        st.info(
            "StockSage is for education only and does not provide personalized "
            "financial, tax, or legal advice."
        )


def render_header() -> None:
    st.title("StockSage")
    st.caption("Ask clear financial questions. Get grounded, beginner-friendly answers.")


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
