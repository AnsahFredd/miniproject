import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HealthMixin:
    def health_check(self) -> Dict[str, Any]:
        if not self.openai_client:
            return {
                "status": "unhealthy",
                "ai_available": False,
                "error": "OpenAI client not initialized - check API key configuration"
            }
        
        try:
            test_response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "ai_available": True,
                "model": self.model,
                "api_responsive": True
            }
        except Exception as e:
            return {
                "status": "degraded", 
                "ai_available": False,
                "error": str(e),
                "fallback_available": True
            }
