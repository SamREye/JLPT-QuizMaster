import json
import hashlib

vocab = None
with open('vocab.json', 'r') as f:
  vocab = json.load(f)
  f.close()

ids = set()
vocab_dict = {}
for expr in vocab:
  for q_type in ["meaning", "reading"]:
    myexpr = expr.copy()
    myexpr_string = f"{json.dumps(myexpr)}/{q_type}"
    # print(myexpr_string)
    # myexpr['id_str'] = myexpr_string
    myid = hashlib.sha256(myexpr_string.encode('utf-8')).hexdigest()[:10]
    # print(myid)
    myexpr['id'] = myid
    if myid in ids:
      print(myexpr_string)
      print("COLLISION")
      exit(0)
    ids.add(myid)
    myexpr['q_type'] = q_type
    vocab_dict[myid] = myexpr

with open('questions.json', 'w') as f:
  json.dump(vocab_dict, f, ensure_ascii=False, indent=2)
  f.close()
