import openai
import logging
from app.core.config import settings

from .analysis import AnalysisMixin
from .qa import QAMixin
from .fallback import FallbackMixin
from .utils import UtilsMixin
from .health import HealthMixin

logger = logging.getLogger(__name__)


class LegalAIService(AnalysisMixin, QAMixin, FallbackMixin, UtilsMixin, HealthMixin):
    """
    Professional Legal AI Service using OpenAI GPT-4
    Combines all mixins into one unified service
    """
    def __init__(self):
        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                logger.warning("OPENAI_API_KEY not found in settings")
                self.openai_client = None
                return

            self.openai_client = openai.OpenAI(api_key=api_key)
            self.model = getattr(settings, 'DEFAULT_AI_MODEL', 'gpt-4')
            self.max_context_length = getattr(settings, 'MAX_CONTEXT_LENGTH', 8000)
            self.temperature = getattr(settings, 'AI_TEMPERATURE', 0.1)
            logger.info(f"Legal AI Service initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Legal AI Service: {e}")
            self.openai_client = None
