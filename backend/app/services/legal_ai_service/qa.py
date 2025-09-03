import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class QAMixin:
    def answer_legal_question(self, question: str, context: str) -> Dict[str, Any]:
        if not self.openai_client:
            return self._fallback_question_answering(question, context)
        
        truncated_context = context[:self.max_context_length] if len(context) > self.max_context_length else context
        
        prompt = f"""You are an expert legal analyst. Based on the following legal document, provide a comprehensive answer to the user's question.

Document content:
{truncated_context}

Question: {question}

Provide a detailed legal analysis addressing:
1. Direct answer to the question
2. Relevant legal principles and concepts
3. Specific document sections that support your answer
4. Potential legal concerns or issues
5. Professional recommendations if applicable

Be specific, cite relevant document parts, and provide professional legal analysis."""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert legal analyst providing detailed document analysis. Be precise, professional, and cite specific document sections when possible."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,
                temperature=self.temperature
            )
            
            ai_answer = response.choices[0].message.content.strip()
            
            return {
                "answer": ai_answer,
                "confidence": 0.95,
                "source": "AI Legal Analysis",
                "model": self.model,
                "question_type": self._classify_question_type(question)
            }
        except Exception as e:
            logger.error(f"AI question answering failed: {e}")
            return self._fallback_question_answering(question, context)
