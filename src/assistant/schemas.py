from pydantic import BaseModel, Field

class TermExplanation(BaseModel):
    term: str = Field(description="Складний термін, знайдений у тексті")
    explanation: str = Field(description="Коротке та зрозуміле пояснення цього терміна")

class QuizQuestion(BaseModel):
    question: str = Field(description="Текст запитання для перевірки знань")
    options: list[str] = Field(description="Список із 4 варіантів відповіді")
    correct_answer: str = Field(description="Правильна відповідь (має точно збігатися з одним із варіантів)")

class StudyAnalysis(BaseModel):
    extracted_text: str = Field(description="Розпізнаний текст із зображення або основні тези")
    explanations: list[TermExplanation] = Field(description="Список знайдених термінів та їх пояснень")
    quiz: list[QuizQuestion] = Field(description="Короткий квіз за матеріалом")