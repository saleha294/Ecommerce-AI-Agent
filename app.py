import streamlit as st
from agent import agent
from errors import LLMBusyError, LLMConfigError, AgentError

# Page title — displayed at the top of the Streamlit app.
st.title("E-Commerce AI Data Agent")

# Chat history — persists across reruns within the same browser session.
# Each entry is {"role": "user"|"assistant", "content": "<text>"}.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Replay all previous messages so the conversation is visible on every rerun.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input — waits for the user to type a question and press Enter.
question = st.chat_input("Ask about products, customers or orders")

if question:
    # Show the user's question immediately and save it to history.
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    # Call the agent and handle any errors with user-friendly messages.
    with st.spinner("Thinking..."):
        try:
            answer = agent(question)
        except LLMBusyError as e:
            answer = "The AI service is busy. Please try again in a moment."
            with st.chat_message("assistant"):
                st.markdown(answer)
                st.caption(str(e))
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.stop()
        except LLMConfigError as e:
            answer = f"There is a configuration problem with the AI service: {e}"
        except AgentError as e:
            answer = f"Something went wrong while processing your question: {e}"

    # Display the assistant's response and save it to history.
    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
