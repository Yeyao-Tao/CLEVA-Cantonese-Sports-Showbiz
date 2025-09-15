# Project: Cantonese (Hong Kong) Film & Actor Benchmark for LLMs — Technical Design

**Owner:** Yeyao Tao

**Status:** Draft v0.1\
**Last updated:** 2025‑09‑15 (Asia/Singapore)

---

## 1) Problem Statement & Goals

Large language models (LLMs) often conflate Mandarin Chinese titles/names with Hong Kong Cantonese. This project builds a *graded benchmark* that tests whether an LLM can:

1. Recognize  Hong Kong Cantonese names of **movies** and **actors**.
2. Handle entity‑relationship queries (e.g., *Which of the following films stars Actor X?*).

### Success Criteria

- A dataset with multiple-choice questions and correct answers, derived from the mappings in `data/entertainment/raw/cgroup_movie.lua` and WikiData data.



### Non‑Goals

- Pronunciation/romanization scoring (Jyutping/Yale) — optional later.
- Audio speech or TTS evaluation.
- OCR/Subtitle parsing.

---

## 2) Data Sources & Language Strategy

### 2.1 Primary Sources

- **Movie JSON mapping** (`data/entertainment/raw/cgroup_movie.lua`). Treat as *ground truth* for film Cantonese names.
- **Wikidata** for structured facts: QIDs, release date (P577), cast (P161), director (P57), country (P495), original language (P364), IMDb ID (P345), awards (P166), etc.

### 2.2 Cantonese Name Retrieval Strategy

Given l10n inconsistencies, use a tiered fallback:

1. **Movies:** use the mapping in `cgroup_movie.lua` as *canonical Hong Kong title*.
2. **Actors:** prefer, in order:\
   a. yue label on Wikidata.

   b. zh‑hk label on Wikidata.

## 3) High‑Level Architecture

Components:

1. **Retrieve JSONLDs from WikiData:** map each film to a unique Wikidata QID; dedupe homonyms (e.g., remakes, TV films). Check `src/cleva/cantonese/wikidata_lookup.py` for how to query WikiData.

2. **Intermediate Data Store:** Consume JSON‑LD from `data/entertainment/intermediate/movie_tripples/*.jsonld`, process in memory, and export intermediate outputs to files in `data/entertainment/intermediate/`.&#x20;

3. **Questions Construction**: Template‑driven MCQs with difficulty tiers; validated distractors. Export MCQs to a JSON file in `data/entertainment/output/`. The question json format needs to match the questsions for sports entities in `data/soccer/output/` exactly.



---

## 4) Data Model

### Dataset (Benchmark) Schema (JSONL)

Currently we have constructed a dataset for sports related questions in Cantonese. For your reference, please check their schema in `data/soccer/output/` . The output of the MCQ json files should be in the same schema as those in `data/soccer/output`. Below is a short snippet of one of the dataset files.

```json
{
  "metadata": {
    "description": "Multiple-choice questions about football player birth years and ages in English and Cantonese",
    "purpose": "Cantonese benchmark for testing LLM understanding of player biographical information",
    "question_types": [
      "player_birth_year",
      "player_current_age",
      "player_youngest",
      "player_oldest"
    ],
    "question_type_distribution": {
      "player_birth_year": 141,
      "player_current_age": 141,
      "player_youngest": 100,
      "player_oldest": 100
    },
    "languages": [
      "English",
      "Cantonese"
    ],
    "total_questions": 482,
    "generation_date": "2025-09-09T00:34:18.005835",
    "format": "Four choices (A, B, C, D) with one correct answer in both languages"
  },
  "questions": [
    {
      "question": "What year was Gareth Bale, the soccer player, born?",
      "question_cantonese": "足球員加里夫巴利係邊年出世？",
      "choices": {
        "A": "1987",
        "B": "1988",
        "C": "1989",
        "D": "1990"
      },
      "choices_cantonese": {
        "A": "1987年",
        "B": "1988年",
        "C": "1989年",
        "D": "1990年"
      },
      "correct_answer": "C",
      "correct_birth_info": {
        "birth_year": 1989,
        "birth_date": "1989-07-16T00:00:00Z",
        "age_in_2025": 36
      },
      "player_info": {
        "name": "Gareth Bale",
        "name_cantonese": "加里夫巴利",
        "id": "Q184586"
      },
      "distractors": [
        "1988",
        "1990",
        "1987"
      ],
      "question_type": "player_birth_year"
    },
...
```

---

## 5) Ingestion & Entity Resolution

### 5.1 Film QID Lookup

- Primary: **Wikidata wbsearchentities** by English title + type filter (film).
- If multiple candidates remain, filter out this film, because we have more than enough data available.

### 5.3 People QIDs

- Resolve via `wbsearchentities` with `type=item` and constraint `occupation` (P106) ∈ {actor (Q33999)} when feasible.
- Prefer candidates that appear as `cast member` (P161) of already‑resolved films to reinforce identity.

---

---

## 7) Question Generation

### 7.1 Difficulty Tiers

- **Easy:** single‑fact recall (release year, director name).
- **Hard:** multi‑hop relations (which film starred Actor X; which actor appeared in Film Y).

### 7.2 Prompting in Cantonese (HK)

- Use **Traditional Chinese** with Cantonese vernacular particles where natural, but keep domain terms formal and unambiguous.
- Examples:
  - Release year: `以下邊套電影係喺{year}年上映？`
  - Actor relation: `以下邊套電影有{actor_hk}參演？`
  - Director relation: `以下邊套電影係{director_hk}執導嘅？ `

### 7.3 Choice Construction & Validation

- Always include **Cantonese titles/names** for all choices.

- **Distractor samplers:**

  - *Adjacent years* (±1–2y) to avoid giveaway.
  - *Same actor different film* or *same director different film* for relation tasks.

- **Hard constraints:**

  - Ensure **exactly one** correct choice given current metadata.
  - For relation questions, verify distractors **do not** satisfy the predicate using the stored edges.



### 7.4 Templates (illustrative)

**T1 — Release Year (movie → year)**

- Prompt: `以下邊套電影係喺{target_year}年上映？`
- Choices: 1 correct (movie with P577 in year), 3 distractors with close years.

**T2 — Actor to Film (actor → film)**

- Prompt: `邊套電影有{actor_hk}參演？`
- Choices: 1 correct from filmography, 3 from same era/genre but not featuring actor.

**T3 — Film to Actor (film → actor)**

- Prompt: `{film_hk}入面邊個有份演出？`
- Choices: 1 correct cast member, 3 distractors drawn from other films in same decade.

**T4 — Director to Film**\
**T5 — Award to Film**\
**T6 — Two‑hop (actor + director)**

Each template captures variables, sampling policy, Cantonese surface forms, and constraints.

---

## 8) Cantonese Name Handling for Actors

### 8.1 Building the Actor Name Map

- For every `cast_qid` encountered, fetch: yue label and zh-hk label. If both are present, use the yue label.
- Generate a file that stores the Cantonese names of all extracted actors. Refer to `data/soccer/cantonese_name_mapping/players_cantonese_names.json` and follow the same schema.

### 8.2 Missing Labels

- If both yue and zh-hk labels are not present for an actor, log them in a seperate file and continue the processing.

## 9) Extensions (Future Work)

- Use IMDB scores or other sources to filter for popular movies only. Currently there are 4000+ movies in the raw dataset, and we don't need all of them.
- Add **TV series** and other art forms.
- Integrate **HKMDB** or **HK Film Archive** as secondary sources for HK‑specific titles.

