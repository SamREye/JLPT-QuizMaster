import sys, csv, json

data_e = []

for level in ["N5", "N4", "N3", "N2", "N1"]:
  with open(f"vocab_list/{level}.csv", "r") as f:
    reader = csv.reader(f)
    first_row = True
    for row in reader:
      if first_row:
        first_row = False
        continue
      data_e.append([level, row[0], row[1], row[2]])
    f.close()
  
data_t = []

for row in data_e:
  if len(row) > 2:
    data_t.append({
      "level": row[0],
      "expression": row[1],
      "reading": row[2],
      "meaning": row[3]
    })

with open(f"vocab.json", "w") as f:
  #convert to utf8
  json.dump(data_t, f, ensure_ascii=False)
  # json.dump(data_t, f)
  f.close()
