import streamlit as st
from core import analyze_study_material

# Налаштування сторінки
st.set_page_config(page_title="Study Assistant", page_icon="📚", layout="centered")

st.title("📚 Віртуальний асистент для навчання")
st.markdown(
    "Завантажте фото вашого конспекту або скриншот тексту, і я допоможу з ним розібратися: виділю головне, поясню складні терміни та згенерую квіз для самоперевірки!")

# --- ІНІЦІАЛІЗАЦІЯ СТАНУ СЕСІЇ (SESSION STATE) ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "chosen_answers" not in st.session_state:
    st.session_state.chosen_answers = {}
if "quiz_version" not in st.session_state:
    st.session_state.quiz_version = 0
if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None
if "mime_type" not in st.session_state:
    st.session_state.mime_type = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# Завантажувач файлів (динамічний ключ дозволяє скидати його з пам'яті)
uploaded_file = st.file_uploader(
    "Оберіть зображення (JPG, PNG)",
    type=["jpg", "jpeg", "png"],
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="Ваш матеріал", width="stretch")

    # Кнопка первинного запуску аналізу
    if st.button("Проаналізувати матеріал", type="primary"):
        with st.spinner("ШІ аналізує документ... Це може зайняти кілька секунд."):
            try:
                # Зберігаємо дані файлу в сесію для можливості регенерації
                st.session_state.image_bytes = uploaded_file.getvalue()
                st.session_state.mime_type = uploaded_file.type

                # Викликаємо ШІ
                st.session_state.analysis_result = analyze_study_material(
                    st.session_state.image_bytes,
                    st.session_state.mime_type
                )
                # Скидаємо старі відповіді квізу, якщо вони були
                st.session_state.quiz_submitted = False
                st.session_state.chosen_answers = {}
                st.session_state.quiz_version += 1

                st.success("Аналіз успішно завершено!")
            except Exception as e:
                st.error(f"Сталася помилка: {e}")

# --- ВІДОБРАЖЕННЯ РЕЗУЛЬТАТІВ ---
if st.session_state.analysis_result:
    result = st.session_state.analysis_result

    # 1. Основні тези
    st.subheader("📝 Основні тези", divider="blue")
    st.write(result.extracted_text)

    # 2. Пояснення термінів
    st.subheader("💡 Пояснення термінів", divider="blue")
    if result.explanations:
        for item in result.explanations:
            st.markdown(f"**{item.term}**: {item.explanation}")
    else:
        st.info("Складних термінів не знайдено.")

    # 3. Інтерактивний квіз
    st.subheader("🎓 Перевірка знань (Квіз)", divider="blue")
    if result.quiz:
        # Форма для відповідей
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(result.quiz, 1):
                st.markdown(f"**Питання {i}:** {q.question}")

                # Унікальний ключ з урахуванням версії скидає вибір при натисканні "Повторити"
                user_answers[i] = st.radio(
                    "Оберіть варіант:",
                    options=q.options,
                    key=f"q_{i}_{st.session_state.quiz_version}",
                    index=None,
                    label_visibility="collapsed"
                )
                st.write("---")

            submitted = st.form_submit_button("Перевірити відповіді")

            if submitted:
                st.session_state.quiz_submitted = True
                st.session_state.chosen_answers = {i: user_answers[i] for i in user_answers}
                st.rerun()

        # --- ВІДОБРАЖЕННЯ РЕЗУЛЬТАТІВ ПЕРЕВІРКИ ТА КНОПОК ДІЙ ---
        if st.session_state.quiz_submitted:
            correct_count = 0
            st.markdown("### 📊 Результати перевірки:")

            for i, q in enumerate(result.quiz, 1):
                selected = st.session_state.chosen_answers.get(i)
                if selected == q.correct_answer:
                    st.success(f"**Питання {i}:** Правильно! ✅ ({q.correct_answer})")
                    correct_count += 1
                elif selected is None:
                    st.warning(f"**Питання {i}:** Ви не обрали відповідь. Правильна: {q.correct_answer}")
                else:
                    st.error(
                        f"**Питання {i}:** Неправильно ❌. Ваша відповідь: {selected}. Правильна: {q.correct_answer}")

            st.info(f"**Загальний рахунок: {correct_count} з {len(result.quiz)}**")

            # Додаємо 3 кнопки дій після проходження
            st.write("---")
            st.markdown("### 🛠️ Що бажаєте зробити далі?")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄 Повторно пройти", use_container_width=True):
                    st.session_state.quiz_version += 1  # Скидає радіокнопки
                    st.session_state.quiz_submitted = False
                    st.session_state.chosen_answers = {}
                    st.rerun()

            with col2:
                if st.button("✨ Нові питання", type="primary", use_container_width=True):
                    with st.spinner("Генеруємо нові питання..."):
                        try:
                            # Повторно викликаємо ШІ для того самого файлу
                            st.session_state.analysis_result = analyze_study_material(
                                st.session_state.image_bytes,
                                st.session_state.mime_type
                            )
                            st.session_state.quiz_version += 1
                            st.session_state.quiz_submitted = False
                            st.session_state.chosen_answers = {}
                            st.rerun()
                        except Exception as e:
                            st.error(f"Помилка регенерації: {e}")

            with col3:
                if st.button("📁 Інший файл", use_container_width=True):
                    # Повне очищення стану до початкового
                    st.session_state.analysis_result = None
                    st.session_state.quiz_submitted = False
                    st.session_state.chosen_answers = {}
                    st.session_state.image_bytes = None
                    st.session_state.mime_type = None
                    st.session_state.uploader_key += 1  # Очищає віджет завантаження файлу
                    st.rerun()
    else:
        st.info("Не вдалося згенерувати квіз.")