import streamlit as st

from auth import is_admin, login, logout
from questions import get_questions, init_db


st.set_page_config(
    page_title="Вопросы студентов | DM Assistant",
    page_icon="📩",
    layout="wide",
)


if not is_admin():
    login()
    st.stop()


st.title("📩 Вопросы студентов")
st.caption("Панель преподавателя · DM Assistant")

if st.button("🚪 Выйти из режима администратора"):
    logout()

st.divider()

init_db()

questions = get_questions()

st.metric("Всего вопросов", len(questions))

if not questions:
    st.info("Пока никто не отправил вопросов.")
else:
    for question in questions:
        question_id, name, topic, text, created_at = question

        with st.expander(
            f"#{question_id} · {name} · {topic}"
        ):
            st.caption(created_at)
            st.write(text)