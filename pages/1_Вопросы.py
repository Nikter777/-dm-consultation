import streamlit as st

from auth import is_admin, logout
from questions import get_questions, init_db


st.set_page_config(
    page_title="Вопросы студентов | DM Assistant",
    page_icon="📩",
    layout="wide",
    initial_sidebar_state="collapsed",
)


if not is_admin():
    st.error("🔒 Доступ только для преподавателя.")

    if st.button("Вернуться на главную"):
        st.switch_page("app.py")

    st.stop()


st.title("📩 Вопросы студентов")
st.caption("Панель преподавателя · DM Assistant")

col1, col2 = st.columns(2)

with col1:
    if st.button(
        "← Вернуться к консультанту",
        use_container_width=True,
    ):
        st.switch_page("app.py")

with col2:
    if st.button(
        "🚪 Выйти из аккаунта",
        use_container_width=True,
    ):
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