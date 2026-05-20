from backend.app.schemas.api import KnowledgeAnswerOut, RetrievedSource
from sqlalchemy.orm import Session


def answer_question(db: Session, question: str, language: str | None = None) -> KnowledgeAnswerOut:
    from backend.app.ai.retrieval.service import retrieve_knowledge

    result = retrieve_knowledge(db, question, language=language, top_k=3)
    answer = result.answer if result.confidence >= 0.35 else "I am not confident enough to answer this automatically."
    return KnowledgeAnswerOut(
        answer=answer,
        confidence=result.confidence,
        sources=[
            RetrievedSource(
                title=item.title,
                section=item.section,
                source_file=item.source_file,
                confidence=item.confidence,
                content_preview=item.content[:220],
            )
            for item in result.sources
        ],
        auto_answer_allowed=result.confidence >= 0.35,
    )
