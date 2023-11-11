from fastapi import FastAPI
import json
from pydantic import BaseModel
import datetime
import os.path
import random

app = FastAPI()

class Outcome(BaseModel):
  level: str
  word: str
  user: str
  passed: bool

@app.get("/vocab/{level}")
def vocab(level):
  """
  Returns a list of vocabulary words for the JLPT level.

  Args:
  level (str): The level of vocabulary to return.

  Returns:
  list: A list of vocabulary word objects ["level", "expression", "reading", "meaning"]
  """
  with open("vocab.json") as f:
    data = json.load(f)
    f.close()
  # filter rows not of same level
  return [row for row in data if row["level"] == level]

@app.put("/record")
def record(outcome: Outcome):
  """
  Records the outcome of a test.

  Args:
  outcome (Outcome): The outcome of the test.

  Returns:
  Status: whether the outcome is recorded successfully.
  """
  user_file = f"users/{outcome.user}.json"
  level = outcome.level
  word = outcome.word
  data = {}
  if not os.path.isfile(user_file):
    with open(user_file, "w") as f:
      f.write("{}")
      f.close()
  else:
    with open(user_file, "r") as f:
      data = json.load(f)
  if level not in data:
    data[level] = {}
  if word not in data[level]:
    data[level][word] = []
  timestamp = int(datetime.datetime.now().timestamp())
  data[level][word].append({
    "timestamp": timestamp,
    "passed": outcome.passed
  })
  with open(user_file, "w") as f:
    json.dump(data, f, ensure_ascii=False)
    f.close()
  return {"status": "OK"}
  
@app.get("/report/{user}/{level}")
def report(user, level):
  """
  Returns a report of the outcomes of a user's tests.
  """
  user_file = f"users/{user}.json"
  if not os.path.isfile(user_file):
    return {"status": "user not found"}
  with open(user_file, "r") as f:
    data = json.load(f)
    f.close()
  report = {}
  for row in data[level]:
    report[row] = grade_datapoint(data[level][row])
  return report

def grade_datapoint(datapoint):
  GRADES = [
    "No Data",
    "Low",
    "Moderate",
    "High",
    "Total"
  ]
  def grade(lvl):
    return {"label": GRADES[lvl], "level": lvl}
  # Keep only the last 5 datapoints
  datapoint = datapoint[-5:]
  mygrade = None
  if len(datapoint) == 0:
    mygrade = grade(0)
  elif len(datapoint) == 1:
    mygrade = grade(3) if datapoint[0]["passed"] else grade(1)
  elif all([x["passed"] for x in datapoint]):
    mygrade = grade(4)
  elif all([x["passed"] for x in datapoint[-3:]]):
    mygrade = grade(3)
  elif all([not x["passed"] for x in datapoint[-3:]]):
    mygrade = grade(1)
  else:
    mygrade = grade(2)
  timestamp = {
    "epoch": datapoint[-1]["timestamp"],
    "datetime": datetime.datetime.fromtimestamp(datapoint[-1]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
  }
  return {"grade": mygrade, "timestamp": timestamp}

SPACING = {
  1: 1 * 24 * 3600,
  2: 3 * 24 * 3600,
  3: 7 * 24 * 3600,
  4: 20 * 24 * 3600
}

def form_quiz(subject, vocab, question_type, answer_type):
  STATEMENT = "What is the {output} for the following {input}?"
  q = {
    "statement": STATEMENT.format(input=question_type, output=answer_type),
    "subject": vocab[subject][question_type],
  }
  c = [vocab[subject][answer_type]]
  for i in range(0, 3):
    c.append(random.choice([vocab[x][answer_type] for x in vocab if vocab[x]["meaning"] not in c]))
  # randomize/shuffle c
  random.shuffle(c)
  q["choices"] = c
  q["answer"] = c.index(vocab[subject][answer_type])
  return q

@app.get("/drill-set/{user}/{level}/{count}")
def drill_set(user, level, count):
  myvocab = vocab(level)
  vocab_dict = {y["expression"]: y for x, y in enumerate(myvocab)}
  myreport = report(user, level)
  questions = []
  leveled = {}
  encountered = myreport.keys()
  notyet = list(set(vocab_dict.keys()) - set(encountered))
  for i in range(1, 5):
    leveled[i] = [x for x in myreport if myreport[x]["grade"]["level"] == i and (myreport[x]["timestamp"]["epoch"] + SPACING[i]) < int(datetime.datetime.now().timestamp())]
  while len(questions) < count:
    for i in range(1, 5):
      if len(leveled[i]) > 0:
        questions.append(random.choice(leveled[i]))
        continue
    break
  while len(questions) < count:
    if len(notyet) > 0:
      index = random.randint(0, len(notyet) - 1)
      questions.append(notyet[index])
      del notyet[index]
      continue
    break
  quiz = []
  for question in questions:
    quiz.append(form_quiz(question, vocab_dict, "expression", "reading"))
  return quiz
      
if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8080)
