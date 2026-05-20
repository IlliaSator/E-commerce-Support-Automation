from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.ai.urgency import detect_language
from backend.app.models import KnowledgeArticle


@dataclass(frozen=True)
class RetrievedChunk:
    title: str
    section: str
    source_file: str
    content: str
    confidence: float


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    answer: str
    confidence: float
    sources: list[RetrievedChunk]


def _fallback_similarity(query: str, content: str) -> float:
    query_terms = {term for term in query.lower().split() if len(term) > 2}
    content_terms = {term for term in content.lower().split() if len(term) > 2}
    if not query_terms:
        return 0.0
    return len(query_terms & content_terms) / len(query_terms)


def retrieve_knowledge(
    db: Session,
    query: str,
    language: str | None = None,
    top_k: int = 3,
) -> RetrievalResult:
    language = language or detect_language(query)
    articles = db.query(KnowledgeArticle).filter(KnowledgeArticle.language == language).all()
    if not articles:
        articles = db.query(KnowledgeArticle).all()
    if not articles:
        return RetrievalResult(query=query, answer="", confidence=0.0, sources=[])

    corpus = [f"{article.title} {article.section} {article.content}" for article in articles]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform(corpus + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    except Exception:
        scores = [_fallback_similarity(query, text) for text in corpus]

    ranked = sorted(enumerate(scores), key=lambda pair: float(pair[1]), reverse=True)[:top_k]
    chunks: list[RetrievedChunk] = []
    for index, score in ranked:
        article = articles[index]
        chunks.append(
            RetrievedChunk(
                title=article.title,
                section=article.section,
                source_file=article.source_file,
                content=article.content,
                confidence=round(float(score), 4),
            )
        )
    confidence = chunks[0].confidence if chunks else 0.0
    answer = chunks[0].content if chunks else ""
    return RetrievalResult(query=query, answer=answer, confidence=confidence, sources=chunks)
