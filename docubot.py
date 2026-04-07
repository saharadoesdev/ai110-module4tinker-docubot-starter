"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob
import re

class DocuBot:
    MIN_USEFUL_SCORE = 2
    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "tell",
        "the",
        "this",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }

    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Split documents into smaller retrieval units
        self.sections = self.build_sections(self.documents)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.sections)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    def split_into_sections(self, text):
        """
        Splits a document into small, consistent sections.

        This uses blank lines as boundaries so each section is usually a
        paragraph or a short markdown block.
        """
        sections = []
        for part in re.split(r"\n\s*\n", text):
            chunk = part.strip()
            if chunk:
                sections.append(chunk)

        if sections:
            return sections

        stripped = text.strip()
        return [stripped] if stripped else []

    def meaningful_tokens(self, text):
        """
        Tokenizes text and removes common stopwords so generic wording does not
        dominate retrieval.
        """
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return [token for token in tokens if token not in self.STOPWORDS]

    def build_sections(self, documents):
        """
        Converts whole documents into section-level retrieval units.
        Returns a list of tuples: (section_id, text)
        """
        sections = []

        for filename, text in documents:
            for section_number, section_text in enumerate(self.split_into_sections(text), start=1):
                section_id = f"{filename}::section_{section_number}"
                sections.append((section_id, section_text))

        return sections

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, sections):
        """
        TODO (Phase 1):
        Build a tiny inverted index mapping lowercase words to the sections
        they appear in.

        Example structure:
        {
            "token": ["AUTH.md", "API_REFERENCE.md"],
            "database": ["DATABASE.md"]
        }

        Keep this simple: split on whitespace, lowercase tokens,
        ignore punctuation if needed.
        """
        index = {}

        for section_id, text in sections:
            tokens = set(self.meaningful_tokens(text))
            for token in tokens:
                if token not in index:
                    index[token] = set()
                index[token].add(section_id)

        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        TODO (Phase 1):
        Return a simple relevance score for how well the text matches the query.

        Suggested baseline:
        - Convert query into lowercase words
        - Count how many appear in the text
        - Return the count as the score
        """
        query_tokens = self.meaningful_tokens(query)
        text_tokens = set(self.meaningful_tokens(text))

        return sum(1 for token in query_tokens if token in text_tokens)

    def retrieve(self, query, top_k=3):
        """
        TODO (Phase 1):
        Use the index and scoring function to select top_k relevant document snippets.

        Return a list of (section_id, text) sorted by score descending.
        """
        scored_results = self.retrieve_scored(query, top_k=top_k)
        return [(section_id, text) for score, section_id, text in scored_results]

    def retrieve_scored(self, query, top_k=3):
        """
        Returns scored retrieval results as (score, section_id, text).

        This keeps the retrieval pipeline explicit: score first, then decide
        whether the evidence is strong enough to answer.
        """
        query_tokens = self.meaningful_tokens(query)

        candidate_sections = set()
        for token in query_tokens:
            if token in self.index:
                candidate_sections.update(self.index[token])

        if candidate_sections:
            candidates = [section for section in self.sections if section[0] in candidate_sections]
        else:
            candidates = []

        results = []
        for section_id, text in candidates:
            score = self.score_document(query, text)
            if score > 0:
                results.append((score, section_id, text))

        results.sort(key=lambda item: (-item[0], item[1]))

        return results[:top_k]

    def has_useful_context(self, scored_snippets, min_score=None):
        """
        Returns True when retrieval found evidence strong enough to answer.
        """
        if min_score is None:
            min_score = self.MIN_USEFUL_SCORE

        if not scored_snippets:
            return False

        best_score, _, _ = scored_snippets[0]
        return best_score >= min_score

    def refusal_message(self):
        return "I don't know based on these docs."

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        """
        snippets = self.retrieve_scored(query, top_k=top_k)

        if not self.has_useful_context(snippets):
            return self.refusal_message()

        formatted = []
        for score, section_id, text in snippets:
            formatted.append(f"[{section_id}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve_scored(query, top_k=top_k)

        if not self.has_useful_context(snippets):
            return self.refusal_message()

        plain_snippets = [(section_id, text) for score, section_id, text in snippets]
        return self.llm_client.answer_from_snippets(query, plain_snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
