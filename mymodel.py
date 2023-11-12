from enum import Enum, IntEnum

from pydantic import BaseModel


class QuestionType(Enum):
  MEANING = "meaning"
  READING = "reading"


class QuestionOutcomeRecord(BaseModel):
  level: str
  expression: str
  q_type: QuestionType
  user: str
  correct: bool


class Grade(IntEnum):
  NODATA = 0
  LOW = 1
  MODERATE = 2
  HIGH = 3
  TOTAL = 4


GRADING_LABELS = {
    Grade.NODATA: "No data",
    Grade.LOW: "Low",
    Grade.MODERATE: "Moderate",
    Grade.HIGH: "High",
    Grade.TOTAL: "Total"
}


class QuestionGrade(BaseModel):
  level: str
  word: str
  user: str
  timestamp: int
  q_type: QuestionType
  grade: Grade


class LevelReport(BaseModel):
  level: str
  user: str
  words: list[QuestionGrade]


class CallStatus(BaseModel):
  status: str
  message: str | None


class QuizQuestion(BaseModel):
  level: str
  subject: str
  q_type: QuestionType
  statement: str
  choices: list[str]
  answer: int


class Quiz(BaseModel):
  questions: list[QuizQuestion]
  user: str
  level: str
