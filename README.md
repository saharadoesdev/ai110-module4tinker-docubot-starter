# DocuBot


## TF Summary
* The core concept students needed to understand

_This Tinker is about preparing data to be sent to an AI system; LLMs perform much better with specific and relevant context. Hallucinations are possible otherwise._

* Where students are most likely to struggle

_I think students are most likely to struggle in Phase 3, where you improve the retrieval mode to make it more specific, because this involves a lot of refactoring as you go from whole files to just sections of the documentation._

* Where AI was helpful vs misleading

_AI was helpful for coming up with ideas for how to implement the retrieval system and then for implementing the easiest ways to do it. However, while it could make suggestions for improving it, you still had to test with lots of different sample questions yourself to see where failures occurred._

* One way they would guide a student without giving the answer

_I would encourage them to use Copilot/Claude to break down anything they're confused about or explain certain output first before just diving in and telling AI to fix the code or implement certain steps._

---

DocuBot is a small documentation assistant that helps answer developer questions about a codebase.  
It can operate in three different modes:

1. **Naive LLM mode**  
   Sends the entire documentation corpus to a Gemini model and asks it to answer the question.

2. **Retrieval only mode**  
   Uses a simple indexing and scoring system to retrieve relevant snippets without calling an LLM.

3. **RAG mode (Retrieval Augmented Generation)**  
   Retrieves relevant snippets, then asks Gemini to answer using only those snippets.

The docs folder contains realistic developer documents (API reference, authentication notes, database notes), but these files are **just text**. They support retrieval experiments and do not require students to set up any backend systems.

---

## Setup

### 1. Install Python dependencies

    pip install -r requirements.txt

### 2. Configure environment variables

Copy the example file:

    cp .env.example .env

Then edit `.env` to include your Gemini API key:

    GEMINI_API_KEY=your_api_key_here

If you do not set a Gemini key, you can still run retrieval only mode.

---

## Running DocuBot

Start the program:

    python main.py

Choose a mode:

- **1**: Naive LLM (Gemini reads the full docs)  
- **2**: Retrieval only (no LLM)  
- **3**: RAG (retrieval + Gemini)

You can use built in sample queries or type your own.

---

## Running Retrieval Evaluation (optional)

    python evaluation.py

This prints simple retrieval hit rates for sample queries.

---

## Modifying the Project

You will primarily work in:

- `docubot.py`  
  Implement or improve the retrieval index, scoring, and snippet selection.

- `llm_client.py`  
  Adjust the prompts and behavior of LLM responses.

- `dataset.py`  
  Add or change sample queries for testing.

---

## Requirements

- Python 3.9+
- A Gemini API key for LLM features (only needed for modes 1 and 3)
- No database, no server setup, no external services besides LLM calls
