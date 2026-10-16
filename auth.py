import hmac

import streamlit as st


def is_admin():
    return st.session_state.get("admin_authenticated", False)


def is_student():
    return st.session_state.get("student_authenticated", False)


def check_password(entered, expected):
    return hmac.compare_digest(
        entered.encode("utf-8"),
        expected.encode("utf-8"),
    )


def login():
    return is_admin()


def student_login():
    if is_student() or is_admin():
        return True

    st.markdown(
        """
        <div style="text-align:center; padding:50px 0 20px;">
            <h1>🧠 DM Assistant</h1>
            <p>ИИ-консультация по дискретной математике</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 2, 1])

    with center:
        with st.form("unified_login_form"):
            password = st.text_input(
                "Код доступа",
                type="password",
            )

            submitted = st.form_submit_button(
                "Продолжить",
                use_container_width=True,
            )

        if submitted:
            admin_password = st.secrets["ADMIN_PASSWORD"]
            student_password = st.secrets["STUDENT_PASSWORD"]

            if check_password(password, admin_password):
                st.session_state.admin_authenticated = True
                st.session_state.student_authenticated = False
                st.rerun()

            elif check_password(password, student_password):
                st.session_state.student_authenticated = True
                st.session_state.admin_authenticated = False
                st.rerun()

            else:
                st.error("Неверный код доступа.")

    return False


def logout():
    st.session_state.admin_authenticated = False
    st.session_state.student_authenticated = False
    st.session_state.messages = []
    st.rerun()


def student_logout():
    logout()