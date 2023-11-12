import datetime
import json
import os.path
import random

from fastapi import FastAPI, HTTPException

import mymodel

app = FastAPI()

LEVELS = ["N1", "N2", "N3", "N4", "N5"]
questions = {}
with open("questions.json") as f:
  questions = json.load(f)
  f.close()
questions_by_level = {}
for level in LEVELS:
  questions_by_level[level] = {
      x: questions[x]
      for x in questions if questions[x]["level"] == level
  }

USER_FILE = "users/{user_id}.json"


def get_user_record(user_id):
  user_file = USER_FILE.format(user_id=user_id)
  user_record = {}
  if not os.path.isfile(user_file):
    set_user_record(user_id, {})
  else:
    with open(user_file, "r") as f:
      user_record = json.load(f)
  return user_record


def set_user_record(user_id, user_record):
  user_file = USER_FILE.format(user_id=user_id)
  with open(user_file, "w") as f:
    json.dump(user_record, f, ensure_ascii=False, indent=2)
    f.close()


@app.get("/record/{user_id}/{question_id}/{correct}")
def record(user_id, question_id, correct):
  """
  Record the user's result--whether correct or not.

  Args:
  - user_id: the user's ID
  - question_id: the ID of the question
  - correct: whether the user got the answer correct

  Returns:
  - status: 200 if the recording was successful
  """
  if correct not in ["true", "false"]:
    raise HTTPException(
        status_code=400,
        detail="invalid correct value: must be either true or false")
  if question_id not in questions:
    raise HTTPException(status_code=404, detail="invalid question id")
  user_record = get_user_record(user_id)
  if question_id not in user_record:
    user_record[question_id] = []
  timestamp = int(datetime.datetime.now().timestamp())
  user_record[question_id].append({
      "timestamp": timestamp,
      "correct": bool(correct == "true")
  })
  set_user_record(user_id, user_record)
  return {"status": "OK"}


def grade_datapoint(datapoint):

  def gen_grade(lvl):
    return {"label": mymodel.GRADING_LABELS[lvl], "level": mymodel.Grade(lvl)}

  # Keep only the last 5 datapoints
  datapoint = datapoint[-5:]
  mygrade = None
  if len(datapoint) == 0:
    mygrade = gen_grade(0)
  elif len(datapoint) == 1:
    mygrade = gen_grade(3) if datapoint[0]["correct"] else gen_grade(1)
  elif all(x["correct"] for x in datapoint):
    mygrade = gen_grade(4)
  elif all(x["correct"] for x in datapoint[-3:]):
    mygrade = gen_grade(3)
  elif all(not x["correct"] for x in datapoint[-3:]):
    mygrade = gen_grade(1)
  else:
    mygrade = gen_grade(2)
  timestamp = datapoint[-1]["timestamp"]
  return {"grade": mygrade, "timestamp": timestamp}


SPACING = {
    1: 1 * 24 * 3600,
    2: 3 * 24 * 3600,
    3: 7 * 24 * 3600,
    4: 20 * 24 * 3600
}


def get_random_choices(q_id):
  q = questions[q_id]
  q_type = q["q_type"]
  level = q["level"]
  choices = []
  while len(choices) < 3:
    rq_id = random.choice(list(questions_by_level[level].keys()))
    choice = questions[rq_id][q_type]
    if choice not in choices:
      choices.append(choice)
  return choices


def form_quiz(q_id):
  q = questions[q_id]
  # STATEMENT = "What is the {q_type} for the following expression?"
  STATEMENT = "表現の{q_type}は何ですか？"
  READING_TR = "読み方"
  MEANING_TR = "意味"
  TR = {"reading": READING_TR, "meaning": MEANING_TR}
  quiz = {
      "statement": STATEMENT.format(q_type=TR[q["q_type"]]),
      "expr": q["expression"],
  }
  answer = q[q["q_type"]]
  c = [answer] + get_random_choices(q_id)
  random.shuffle(c)
  quiz["choices"] = c
  quiz["answer"] = c.index(answer)
  quiz["question_id"] = q_id
  return quiz


def needs_repetition(record):
  grade = grade_datapoint(record)
  space_since = int(datetime.datetime.now().timestamp()) - grade["timestamp"]
  if space_since > SPACING[grade["grade"]["level"]]:
    return True
  return False


@app.get("/next/{user_id}/{level}")
def next(user_id, level):
  """
  Get the next set of questions to be taken for the given user and level.

  Args:
  - user_id: id of the user
  - level: level of the quiz

  Returns:
  - quiz: array of mutliple choice questions
  """
  count = 1
  global questions
  global questions_by_level
  record = get_user_record(user_id)
  seen_ids = []
  for q_id in record:
    if questions[q_id]["level"] == level:
      seen_ids.append(q_id)
  unseen_ids = list(questions_by_level[level].keys() - record.keys())
  to_ask = []
  while len(to_ask) < count:
    for seen_id in seen_ids:
      if seen_id not in to_ask:
        if needs_repetition(record[seen_id]):
          to_ask.append(seen_id)
          continue
        else:
          pass
    break
  while len(to_ask) < count:
    to_ask.append(random.choice(unseen_ids))
  quiz = []
  for q_id in to_ask:
    quiz.append(form_quiz(q_id))
  return quiz


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8080)
