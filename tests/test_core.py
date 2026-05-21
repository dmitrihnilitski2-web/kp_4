import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Додаємо шлях до папки src/assistant, щоб імпорти працювали коректно
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/assistant')))

from core import analyze_study_material
from schemas import StudyAnalysis, TermExplanation, QuizQuestion
from google.genai.errors import APIError

# 1. Тест успішного виконання
@patch('core.client.models.generate_content')
def test_analyze_study_material_success(mock_generate_content):
    mock_response = MagicMock()
    mock_response.parsed = StudyAnalysis(
        extracted_text="Це тестовий конспект з фізики.",
        explanations=[TermExplanation(term="Гравітація", explanation="Притягання тіл.")],
        quiz=[QuizQuestion(question="Що таке гравітація?", options=["А", "Б", "В", "Г"], correct_answer="А")]
    )
    mock_generate_content.return_value = mock_response

    result = analyze_study_material(b"fake_image_bytes")

    assert result.extracted_text == "Це тестовий конспект з фізики."
    assert len(result.quiz) == 1
    assert result.quiz[0].correct_answer == "А"

# 2. Тест обробки лімітів (429 Resource Exhausted)
@patch('core.client.models.generate_content')
def test_analyze_study_material_429_error(mock_generate_content):
    # Додаємо порожній словник {} як обов'язковий аргумент response_json
    mock_error = APIError("Resource Exhausted Error", {})
    mock_error.code = 429
    mock_error.message = "Resource Exhausted Error"
    mock_generate_content.side_effect = mock_error

    with pytest.raises(RuntimeError, match="Перевищено ліміт запитів"):
        analyze_study_material(b"fake_image_bytes")

# 3. Тест обробки невалідних даних (400 Invalid Argument)
@patch('core.client.models.generate_content')
def test_analyze_study_material_400_error(mock_generate_content):
    # Додаємо порожній словник {} як обов'язковий аргумент response_json
    mock_error = APIError("Invalid Argument Error", {})
    mock_error.code = 400
    mock_error.message = "Invalid Argument Error"
    mock_generate_content.side_effect = mock_error

    with pytest.raises(RuntimeError, match="Невірні дані"):
        analyze_study_material(b"fake_image_bytes")