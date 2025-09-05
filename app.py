import streamlit as st
import requests

API_URL = "https://cortex-bot-backend-1.onrender.com/chat"

st.set_page_config(page_title="Snowflake Cortex Analyst Chatbot", layout="wide")

st.title("🤖 Snowflake Cortex Analyst Chatbot")

# Keep chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_suggestion" not in st.session_state:
    st.session_state.pending_suggestion = None

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# If user clicked a suggestion earlier, use that as input
user_query = None
if st.session_state.pending_suggestion:
    user_query = st.session_state.pending_suggestion
    st.session_state.pending_suggestion = None
else:
    user_query = st.chat_input("Ask about inventory...")

if user_query:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Get Cortex Analyst response
    with st.chat_message("assistant"):
        with st.spinner("Querying Snowflake Cortex Analyst..."):
            try:
                resp = requests.post(API_URL, json={"user_query": user_query}, timeout=60)
                resp.raise_for_status()
                data = resp.json()

                # Build assistant response text
                answer_text = ""
                if data.get("answer"):
                    answer_text += f"**💡 Interpretation**\n\n{data['answer']}\n\n"

                if data.get("sql"):
                    answer_text += "📄 **Generated SQL**\n"
                    answer_text += f"```sql\n{data['sql']}\n```\n\n"

                results = data.get("results", [])
                if results and isinstance(results, list):
                    st.subheader("📊 Results")
                    st.dataframe(results)
                else:
                    st.warning("⚠️ No results returned from query.")

                # Suggestions (now clickable)
                if data.get("suggestions"):
                    answer_text += "**💡 Suggested Questions**\n"
                    for i, s in enumerate(data["suggestions"]):
                        if st.button(s, key=f"suggestion_{len(st.session_state.messages)}_{i}"):
                            st.session_state.pending_suggestion = s
                            st.rerun()

                # Warnings
                if data.get("warnings"):
                    answer_text += "**⚠️ Warnings**\n"
                    for w in data["warnings"]:
                        answer_text += f"- {w}\n"

                st.markdown(answer_text)
                st.session_state.messages.append({"role": "assistant", "content": answer_text})

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
