# GRE JSON Canonical Schema

Questo file definisce il formato canonico dei dati per il portale GRE.

## Sezioni supportate

- verbal
- quant
- writing

## Categorie supportate

### Verbal
- reading_comprehension
- text_completion
- sentence_equivalence

### Quant
- quantitative_comparison
- problem_solving
- data_interpretation

### Writing
- analytical_writing

---

## Regole generali

Ogni file JSON di sezione contiene un array di item.

Ogni item GRE deve avere:
- `id`
- `category`
- `itemType`
- `prompt`

Campi opzionali ma consigliati:
- `instruction`
- `explanation`

---

## 1) mcq_single

Usato per:
- Verbal single-answer
- Problem Solving single-answer
- Quantitative Comparison
- eventuali Data Interpretation single-answer

Struttura canonica:

```json
{
  "id": "Q1-001",
  "category": "problem_solving",
  "instruction": "Select one answer choice.",
  "itemType": "mcq_single",
  "prompt": "If x = 3 and y = 5, what is the value of 2x + y?",
  "choices": {
    "A": "8",
    "B": "10",
    "C": "11",
    "D": "13"
  },
  "optionOrder": ["A", "B", "C", "D"],
  "correct": "C",
  "explanation": "2(3) + 5 = 11."
}