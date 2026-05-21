import os
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv
from pydantic import ValidationError

# Імпортуємо наші моделі даних з сусіднього файлу
from schemas import StudyAnalysis

# Завантажуємо змінні середовища з файлу .env (зокрема GEMINI_API_KEY)
load_dotenv()

# Отримуємо ключ та ініціалізуємо клієнта
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY не знайдено. Перевірте файл .env.")

client = genai.Client(api_key=api_key)

# Системна інструкція визначає роль та поведінку моделі
SYSTEM_INSTRUCTION = """
Ти — розумний асистент для студентів (Multimodal Study Assistant).
Твоє завдання — проаналізувати надане зображення (фото конспекту або скриншот тексту).
1. Розпізнай та виділи основний текст/тези.
2. Знайди складні терміни та поясни їх простою мовою.
3. Згенеруй короткий квіз (мінімум 3 питання) за цим матеріалом.
Відповідай виключно українською мовою.
"""


def analyze_study_material(image_bytes: bytes, mime_type: str = "image/jpeg") -> StudyAnalysis:
    """
    Відправляє зображення до Gemini та повертає структурований аналіз (JSON -> Pydantic).
    """
    try:
        # Налаштування параметрів генерації згідно з вимогами
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,  # Додає креативності для генерації цікавих квізів
            top_p=0.9,  # Допомагає уникнути відхилень від фактів
            response_mime_type="application/json",
            response_schema=StudyAnalysis,  # Structured Output через Pydantic
        )

        # Формуємо об'єкт зображення для відправки
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type
        )

        # Виклик моделі (оновлено до версії 2.5-flash)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[image_part, "Проаналізуй цей конспект та згенеруй відповідь."],
            config=config
        )

        # Повертаємо вже розпарсений Pydantic-об'єкт (відбувається автовалідація JSON)
        if response.parsed:
            return response.parsed
        else:
            raise ValueError("Модель не повернула структурованих даних.")

    # Обробка помилок згідно з вимогами (try...except)
    except APIError as e:
        if e.code == 429:
            raise RuntimeError("Помилка: Перевищено ліміт запитів (Resource Exhausted). Спробуйте пізніше.")
        elif e.code == 400:
            raise RuntimeError(f"Помилка: Невірні дані (InvalidArgument). Деталі: {e.message}")
        else:
            raise RuntimeError(f"Помилка API Gemini: {e.message}")
    except ValidationError as e:
        raise RuntimeError(f"Помилка валідації даних (модель повернула неправильний формат): {e}")
    except Exception as e:
        raise RuntimeError(f"Непередбачена помилка: {e}")