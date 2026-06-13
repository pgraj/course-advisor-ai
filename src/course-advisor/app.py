import streamlit as st
from course_advisor.advisor import handle_message

st.set_page_config(page_title="HIAS Course Advisor", page_icon="🎓")
st.title("🎓 HIAS Course Advisor")


# Initialise state on first load
if "chat_state" not in st.session_state:
    st.session_state.chat_state = {
        "education_level": None, "interests": [], "career_goal": None
    }
if "messages" not in st.session_state:
    st.session_state.messages = []



# Sidebar: live profile + reset
with st.sidebar:
    st.header("Your Profile")
    st.write("**Education:**", st.session_state.chat_state["education_level"] or "_not set_")
    st.write("**Interests:**", ", ".join(st.session_state.chat_state["interests"]) or "_none_")
    st.write("**Career goal:**", st.session_state.chat_state["career_goal"] or "_not set_")
    if st.button("Reset conversation"):
        st.session_state.clear()
        st.rerun()

# Replay history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input box
if prompt := st.chat_input("Ask about courses, fees, or recommendations..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply, st.session_state.chat_state = handle_message(prompt, st.session_state.chat_state)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})