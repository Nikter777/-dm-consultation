import base64
import hashlib

import streamlit as st
from google import genai
from google.genai import types

from auth import student_login, student_logout


st.set_page_config(
    page_title="DM Assistant | Дискретная математика",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


MODEL = "gemini-3.5-flash-lite"

MAX_IMAGE_SIZE = 10 * 1024 * 1024

MAX_HISTORY_MESSAGES = 30

SYSTEM_PROMPT = """
Ты — DM Assistant, учебный ИИ-консультант по дискретной математике
для студентов факультета компьютерных наук НИУ ВШЭ.

Твоя задача — помогать студентам понимать материал, разбирать
домашние задания, проверять доказательства и готовиться к контрольным.

Правила:

1. Всегда отвечай на русском языке.
2. Объясняй математические понятия понятно, но строго.
3. Используй LaTeX для математических формул.
4. При проверке доказательств анализируй каждый логический переход.
5. Если студент допустил ошибку, объясняй, где именно она находится.
6. Не выдумывай условия задач, определения или содержимое фотографий.
7. Если фотография нечёткая, попроси прислать более качественную.
8. Если не уверен в решении, прямо сообщи об этом.
9. Не выдавай предположения за доказанные математические факты.
10. Если студент не понимает объяснение, предложи более простой пример.
11. При необходимости задавай наводящие вопросы.
12. Если вопрос невозможно уверенно разрешить, предложи обратиться
к преподавателю в Telegram.
13. Если студент прислал фотографию решения, сначала внимательно
прочитай условие и все видимые математические выражения.
14. Не утверждай, что решение верное, пока не проверишь переходы.
15. Если условие на фотографии не видно, не восстанавливай его
по догадкам.
16. Не подменяй дискретную математику математическим анализом,
если студент явно не просит об этом.
17. Если студент просит только подсказку, не раскрывай сразу
полное решение.
18. Не утверждай, что имеешь доступ к оценкам, ведомостям
или личным данным студентов.
"""


st.markdown(
    """
    <style>
    .stApp {
        background: #ffffff;
        color: #202638;
    }

    [data-testid="stSidebar"] {
        background: #f7f8fc;
        border-right: 1px solid #e6e8f0;
    }

    [data-testid="stChatMessage"] {
        background: #f7f8fc;
        border: 1px solid #e6e8f0;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .hero {
        text-align: center;
        padding: 35px 0 25px;
    }

    .hero h1 {
        font-size: clamp(1.7rem, 4vw, 2.4rem);
        font-weight: 750;
        margin-bottom: 12px;
        color: #202638;
    }

    .hero p {
        color: #667085;
        font-size: 1.05rem;
    }

    .status {
        display: inline-block;
        background: #e9f8ef;
        color: #167347;
        padding: 7px 16px;
        border-radius: 30px;
        font-size: 0.85rem;
        margin-top: 12px;
    }

    .stButton > button {
        background: #ffffff;
        color: #202638;
        border: 1px solid #dce0eb;
        border-radius: 12px;
        min-height: 48px;
        font-weight: 500;
    }

    .stButton > button:hover {
        background: #f0eeff;
        color: #5745d5;
        border-color: #6757e8;
    }

    [data-testid="stFileUploader"] {
        background: #ffffff;
        border-radius: 12px;
    }

    [data-testid="stChatInput"] {
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if not student_login():
    st.stop()


@st.cache_resource
def get_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


def encode_image(data):
    return base64.b64encode(data).decode("utf-8")


def decode_image(data):
    return base64.b64decode(data)


def build_contents(messages):
    contents = []

    for message in messages:
        parts = []

        if message.get("content"):
            parts.append(
                types.Part.from_text(
                    text=message["content"]
                )
            )

        if message.get("image"):
            parts.append(
                types.Part.from_bytes(
                    data=decode_image(message["image"]),
                    mime_type=message["mime_type"],
                )
            )

        if not parts:
            continue

        contents.append(
            types.Content(
                role=(
                    "user"
                    if message["role"] == "user"
                    else "model"
                ),
                parts=parts,
            )
        )

    return contents


def clear_chat():
    st.session_state.messages = []
    st.session_state.pending_prompt = None
    st.session_state.last_image_id = None
    st.session_state.uploader_version += 1


def generate_answer(messages):
    client = get_client()

    response = client.models.generate_content(
        model=MODEL,
        contents=build_contents(messages),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )

    if not response.text:
        return (
            "Не удалось получить содержательный ответ. "
            "Попробуй переформулировать вопрос."
        )

    return response.text


if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "uploader_version" not in st.session_state:
    st.session_state.uploader_version = 0

if "last_image_id" not in st.session_state:
    st.session_state.last_image_id = None


with st.sidebar:
    st.title("🧠 DM Assistant")

    st.caption(
        "ФКН ВШЭ · Дискретная математика"
    )

    st.divider()

    st.subheader("Навигация")

    st.button(
        "➕ Новый диалог",
        use_container_width=True,
        on_click=clear_chat,
    )

    st.divider()

    st.subheader("📷 Фотография решения")

    uploaded_file = st.file_uploader(
        "Прикрепи изображение",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
        key=f"image_{st.session_state.uploader_version}",
    )

    if uploaded_file is not None:
        if uploaded_file.size > MAX_IMAGE_SIZE:
            st.error(
                "Размер изображения не должен превышать 10 МБ."
            )
            uploaded_file = None
        else:
            st.image(
                uploaded_file,
                caption="Прикреплённое решение",
            )

    st.divider()

    st.subheader("💬 Связь с преподавателем")

    st.caption(
        "ИИ может допускать ошибки. "
        "Если остались вопросы по домашнему заданию, "
        "оценке или решению задачи, напиши преподавателю."
    )

    st.link_button(
        "✉️ Написать в Telegram",
        "https://t.me/nikter777",
        use_container_width=True,
    )

    st.divider()

    st.subheader("📊 Диалог")

    st.write(
        f"Сообщений: {len(st.session_state.messages)}"
    )

    st.divider()

    st.button(
        "🚪 Выйти",
        use_container_width=True,
        on_click=student_logout,
    )

    st.divider()

    st.caption(
        "Ответы ИИ могут содержать ошибки. "
        "Проверяй важные математические утверждения."
    )


if not st.session_state.messages:
    st.markdown(
        """
        <div class="hero">
            <h1>Дискретная математика 🧠</h1>
            <p>
                Твой персональный ИИ-помощник
                для подготовки к контрольной работе
            </p>
            <span class="status">
                ● ИИ-консультант доступен
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    st.write("### С чего начнём?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "📚 Объясни кванторы",
            use_container_width=True,
        ):
            st.session_state.pending_prompt = (
                "Объясни кванторы всеобщности и существования "
                "с примерами."
            )
            st.rerun()

        if st.button(
            "🧩 Разберём логические формулы",
            use_container_width=True,
        ):
            st.session_state.pending_prompt = (
                "Объясни основные логические операции "
                "и эквивалентные преобразования формул."
            )
            st.rerun()

    with col2:
        if st.button(
            "✍️ Проверь моё доказательство",
            use_container_width=True,
        ):
            st.session_state.pending_prompt = (
                "Помоги проверить моё доказательство. "
                "Сначала попроси прислать само решение."
            )
            st.rerun()

        if st.button(
            "🎯 Подготовка к контрольной",
            use_container_width=True,
        ):
            st.session_state.pending_prompt = (
                "Помоги мне подготовиться к контрольной "
                "по дискретной математике. "
                "Сначала уточни темы и мой уровень подготовки."
            )
            st.rerun()


for message in st.session_state.messages:
    with st.chat_message(
        message["role"],
        avatar=(
            "🧑‍🎓"
            if message["role"] == "user"
            else "🧠"
        ),
    ):
        if message.get("content"):
            st.markdown(message["content"])

        if message.get("image"):
            st.image(
                decode_image(message["image"])
            )


prompt = st.chat_input(
    "Спроси что-нибудь по дискретной математике..."
)

if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None


image_data = None
mime_type = None
image_id = None

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()

    image_id = hashlib.sha256(
        image_bytes
    ).hexdigest()

    if image_id != st.session_state.last_image_id:
        image_data = encode_image(image_bytes)
        mime_type = uploaded_file.type


if prompt or image_data:
    if not prompt:
        prompt = "Пожалуйста, разбери решение на фотографии."

    user_message = {
        "role": "user",
        "content": prompt,
        "image": image_data,
        "mime_type": mime_type,
    }

    with st.chat_message(
        "user",
        avatar="🧑‍🎓",
    ):
        st.markdown(prompt)

        if image_data:
            st.image(
                decode_image(image_data)
            )

    with st.chat_message(
        "assistant",
        avatar="🧠",
    ):
        with st.spinner("Анализирую задачу..."):
            try:
                history = (
                    st.session_state.messages[
                        -MAX_HISTORY_MESSAGES:
                    ]
                )

                answer = generate_answer(
                    history + [user_message]
                )

                st.markdown(answer)

                st.session_state.messages.append(
                    user_message
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

                if image_data:
                    st.session_state.last_image_id = image_id

            except Exception:
                st.error(
                    "Не удалось получить ответ от ИИ. "
                    "Попробуй ещё раз немного позже."
                )