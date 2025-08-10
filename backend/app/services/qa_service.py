from datetime import datetime
import os
import logging
from pathlib import Path
import re
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
import torch
from typing import Dict, List, Optional
from app.models.document import AcceptedDocument
from bson import ObjectId
from app.core.runtime import setup_runtime
from app.utils.hf_cache import load_pipeline_with_cache


setup_runtime()

logger = logging.getLogger(__name__)


# Prefer config but keep loose coupling for environments without settings import
try:
    from app.core.config import settings
except Exception:
    settings = None

def resolve_general_qa() -> str:
    env_id = os.getenv("QA_MODEL")
    if env_id:
        return env_id
    if settings and getattr(settings, "QA_MODEL", None):
        return str(settings.QA_MODEL)
    return "AnsahFredd/qa_model"  # small default

def resolve_legal_qa() -> str:
    env_id = os.getenv("LEGAL_QA_MODEL")
    if env_id:
        return env_id
    if settings and getattr(settings, "LEGAL_QA_MODEL", None):
        return str(settings.LEGAL_QA_MODEL)
    # deepset/roberta-base-squad2 is good but heavy; prefer small fallback first
    return "AnsahFredd/legal_qa_model"

GENERAL_QA_ID = resolve_general_qa()
LEGAL_QA_ID = resolve_legal_qa()

class QuestionAnsweringService:
    def __init__(self):
        self.documents = {}
        self.general_qa_pipeline = None
        self.legal_qa_pipeline = None
        self.general_qa_model_name = GENERAL_QA_ID
        self.legal_qa_model_name = LEGAL_QA_ID

        self.legal_keywords = {
            'contract', 'agreement', 'clause', 'legal', 'law', 'court', 'case', 'defendant',
            'plaintiff', 'liability', 'breach', 'damages', 'jurisdiction', 'statute',
            'regulation', 'compliance', 'terms', 'conditions', 'warranty', 'indemnity',
            'termination', 'penalty', 'arbitration', 'litigation', 'patent', 'copyright',
            'trademark', 'intellectual property', 'confidentiality', 'non-disclosure'
        }
        logger.info(f"QA service initialized. General={self.general_qa_model_name} Legal={self.legal_qa_model_name}")

    def _load_general_qa_model(self):
        if self.general_qa_pipeline is not None:
            return
        pl, used = load_pipeline_with_cache(
            "question-answering",
            self.general_qa_model_name,
            local_model_path="ai/models/roberta-base-squad2",
            fallbacks=["distilbert-base-cased-distilled-squad"],
            device=-1,
        )
        if pl is None:
            raise RuntimeError("Failed to load general QA pipeline.")
        if used and used != self.general_qa_model_name:
            logger.warning(f"General QA fell back to {used}")
        self.general_qa_pipeline = pl

    def _load_legal_qa_model(self):
        if self.legal_qa_pipeline is not None:
            return
        pl, used = load_pipeline_with_cache(
            "question-answering",
            self.legal_qa_model_name,
            local_model_path="ai/models/legal-bert-base-uncased",
            # fall back to general small QA if legal model is too heavy
            fallbacks=["deepset/roberta-base-squad2", "distilbert-base-cased-distilled-squad"],
            device=-1,
        )
        if pl is None:
            raise RuntimeError("Failed to load legal QA pipeline.")
        if used and used != self.legal_qa_model_name:
            logger.warning(f"Legal QA fell back to {used}")
        self.legal_qa_pipeline = pl

    def _is_legal_question(self, question: str, context: str = "") -> bool:
        text = (question + " " + context).lower()
        return sum(1 for k in self.legal_keywords if k in text) >= 2

    def _select_qa_pipeline(self, question: str, context: str = ""):
        if self._is_legal_question(question, context):
            try:
                self._load_legal_qa_model()
                return self.legal_qa_pipeline, "legal"
            except Exception as e:
                logger.warning(f"Legal QA unavailable: {e}")
                self._load_general_qa_model()
                return self.general_qa_pipeline, "general"
        else:
            try:
                self._load_general_qa_model()
                return self.general_qa_pipeline, "general"
            except Exception as e:
                logger.warning(f"General QA unavailable: {e}")
                self._load_legal_qa_model()
                return self.legal_qa_pipeline, "legal"

    def add_document(self, doc_id: str, content: str):
        self.documents[doc_id] = content

    async def load_document_from_db(self, document_id: str, user_id: str) -> Optional[str]:
        if document_id in self.documents:
            return self.documents[document_id]
        try:
            document = await AcceptedDocument.find_one({"_id": ObjectId(document_id), "user_id": user_id})
            if document and getattr(document, "content", None):
                self.documents[document_id] = document.content
                return document.content
        except Exception as e:
            logger.error(f"Error loading document {document_id}: {e}")
        return None

    async def answer_question(self, question: str, user_id: str, document_id: Optional[str] = None) -> Dict:
        try:
            if document_id:
                context = await self.load_document_from_db(document_id, user_id)
                source = document_id if context else None
            else:
                context, source = await self._find_best_context_from_db(question, user_id)

            if not context:
                return {
                    "answer": "No documents available to answer the question.",
                    "confidence_score": 0.0,
                    "source_document": None,
                    "model_used": None
                }

            qa_pipeline, model_type = self._select_qa_pipeline(question, context)
            result = qa_pipeline(question=question, context=context)

            if source:
                await self._track_question_answer(
                    document_id=source,
                    question=question,
                    answer=result.get("answer"),
                    confidence_score=result.get("score", 0.0),
                    model_used=model_type,
                )

            return {
                "answer": result.get("answer"),
                "confidence_score": result.get("score", 0.0),
                "source_document": source,
                "model_used": model_type
            }

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "confidence_score": 0.0,
                "source_document": None,
                "model_used": None
            }

    async def _track_question_answer(self, document_id: str, question: str, answer: str, confidence_score: float, model_used: str):
        try:
            doc = await AcceptedDocument.find_one({"_id": ObjectId(document_id)})
            if doc:
                qa_record = {
                    "question": question,
                    "answer": answer,
                    "confidence_score": confidence_score,
                    "model_used": model_used,
                    "asked_at": datetime.utcnow(),
                    "id": str(ObjectId())
                }
                if getattr(doc, "questions_asked", None) is None:
                    doc.questions_asked = []
                doc.questions_asked.append(qa_record)
                await doc.save()
        except Exception as e:
            logger.error(f"Failed to track Q&A: {e}")

    async def _find_best_context_from_db(self, question: str, user_id: str) -> tuple:
        try:
            documents = await AcceptedDocument.find(AcceptedDocument.user_id == user_id).to_list()
            if not documents:
                return "", None

            best_score = 0.0
            best_context = ""
            best_doc_id = None

            qa_pipeline, _ = self._select_qa_pipeline(question)
            for doc in documents:
                content = getattr(doc, "content", None)
                if not content:
                    continue
                try:
                    result = qa_pipeline(question=question, context=content)
                    score = float(result.get("score", 0.0))
                    if score > best_score:
                        best_score = score
                        best_context = content
                        best_doc_id = str(doc.id)
                        self.documents[str(doc.id)] = content
                except Exception as e:
                    logger.warning(f"Scoring doc {getattr(doc, 'id', '?')} failed: {e}")
                    continue

            return best_context, best_doc_id
        except Exception as e:
            logger.error(f"Error finding best context: {e}")
            return "", None

    def get_model_info(self) -> dict:
        return {
            "general_model": {"type": self.general_qa_model_name, "loaded": self.general_qa_pipeline is not None},
            "legal_model": {"type": self.legal_qa_model_name, "loaded": self.legal_qa_pipeline is not None},
            "pipeline_task": "question-answering",
            "cache_dir": os.getenv("TRANSFORMERS_CACHE"),
        }

qa_service = QuestionAnsweringService()
