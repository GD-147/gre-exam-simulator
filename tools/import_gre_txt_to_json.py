import re
import json
import argparse
from pathlib import Path

ID_RE = re.compile(r"^(V|Q)\d{1,2}-\d{3}\s*$")
KEY_START_RE = re.compile(
    r"^(?P<id>(?:V|Q)\d{1,2}-\d{3})\s*[-–—]+\s*Correct:\s*(?P<correct>.+?)\s*[-–—]+\s*Explanation:\s*(?P<exp>.*)\s*$"
)
OPTION_RE = re.compile(r"^([A-I])\)\s*(.*)\s*$")


def split_questions_and_key(lines):
    key_idx = None
    for i, line in enumerate(lines):
        if KEY_START_RE.match(line.strip()):
            key_idx = i
            break
    if key_idx is None:
        return lines, []
    return lines[:key_idx], lines[key_idx:]


def parse_key_blocks(key_lines):
    key_map = {}
    cur_id = None
    cur_correct = None
    cur_exp_parts = []

    def flush():
        nonlocal cur_id, cur_correct, cur_exp_parts
        if cur_id:
            key_map[cur_id] = {
                "correct_raw": (cur_correct or "").strip(),
                "explanation": " ".join(p.strip() for p in cur_exp_parts if p.strip()).strip()
            }
        cur_id = None
        cur_correct = None
        cur_exp_parts = []

    for raw in key_lines:
        line = raw.rstrip("\n")
        m = KEY_START_RE.match(line.strip())
        if m:
            flush()
            cur_id = m.group("id").strip()
            cur_correct = m.group("correct").strip()
            exp0 = m.group("exp").strip()
            if exp0:
                cur_exp_parts.append(exp0)
        else:
            if cur_id and line.strip():
                cur_exp_parts.append(line.strip())

    flush()
    return key_map


def parse_questions(q_lines):
    i = 0
    questions = []

    while i < len(q_lines):
        line = q_lines[i].strip()
        if not ID_RE.match(line):
            i += 1
            continue

        qid = line
        i += 1

        category = ""
        instruction = ""
        item_type = ""
        prompt_lines = []
        choices = {}
        numeric_entry = False

        while i < len(q_lines):
            cur = q_lines[i].rstrip("\n")
            stripped = cur.strip()

            if ID_RE.match(stripped):
                break

            if stripped.startswith("Category:"):
                category = stripped.split(":", 1)[1].strip()
                i += 1
                continue

            if stripped.startswith("Instruction:"):
                instruction = stripped.split(":", 1)[1].strip()
                i += 1
                continue

            if stripped.startswith("ItemType:"):
                item_type = stripped.split(":", 1)[1].strip()
                i += 1
                continue

            if stripped == "Prompt:":
                i += 1
                while i < len(q_lines):
                    cur2 = q_lines[i].rstrip("\n")
                    stripped2 = cur2.strip()

                    if stripped2 == "Answer:":
                        numeric_entry = True
                        i += 1
                        if i < len(q_lines) and q_lines[i].strip():
                            i += 1
                        break

                    if ID_RE.match(stripped2):
                        break

                    mopt = OPTION_RE.match(stripped2)
                    if mopt:
                        break

                    prompt_lines.append(cur2)
                    i += 1

                while i < len(q_lines):
                    stripped3 = q_lines[i].strip()

                    if not stripped3:
                        i += 1
                        continue

                    mopt = OPTION_RE.match(stripped3)
                    if not mopt:
                        break

                    choices[mopt.group(1)] = mopt.group(2).strip()
                    i += 1

                continue

            i += 1

        prompt = "\n".join(line.rstrip() for line in prompt_lines).strip()

        q = {
            "id": qid,
            "category": category,
            "instruction": instruction,
            "itemType": item_type,
            "prompt": prompt,
        }

        if item_type == "numeric_entry" or numeric_entry:
            q["itemType"] = "numeric_entry"
        else:
            q["choices"] = choices
            q["optionOrder"] = list(choices.keys())

        questions.append(q)

    return questions


def attach_answers(questions, key_map):
    missing = []

    for q in questions:
        qid = q["id"]
        key = key_map.get(qid)
        if not key:
            missing.append(qid)
            q["explanation"] = ""
            if q.get("itemType") == "numeric_entry":
                q["numericAnswers"] = []
            elif q.get("itemType") == "mcq_multi":
                q["correctAnswers"] = []
            else:
                q["correct"] = ""
            continue

        raw = key["correct_raw"]
        q["explanation"] = key["explanation"]

        if q.get("itemType") == "numeric_entry":
            q["numericAnswers"] = [raw]
        elif q.get("itemType") == "mcq_multi":
            parts = [p.strip() for p in raw.split("+")]
            q["correctAnswers"] = parts
        else:
            q["correct"] = raw.strip()

    return questions, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True)
    ap.add_argument("--outfile", required=True)
    ap.add_argument("--expected", type=int, default=None)
    args = ap.parse_args()

    txt = Path(args.infile).read_text(encoding="utf-8", errors="replace")
    lines = txt.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    q_lines, key_lines = split_questions_and_key(lines)
    questions = parse_questions(q_lines)
    key_map = parse_key_blocks(key_lines)
    merged, missing = attach_answers(questions, key_map)

    if args.expected is not None and len(merged) != args.expected:
        print(f"WARNING: expected {args.expected} questions, found {len(merged)}")

    if missing:
        print("WARNING: Missing key entries for:", ", ".join(missing))

    out_path = Path(args.outfile)
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {len(merged)} questions to {out_path}")


if __name__ == "__main__":
    main()