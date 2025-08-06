from datetime import date, datetime
import re
from typing import Any, Dict, Optional
from openai import OpenAI

from app.models.user import User
from app.models.document import Document
from app.dependencies.auth import get_current_user
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def extract_dates_with_regex(text: str) -> list:
    """Extract potential dates using regex patterns"""
    date_patterns = [
        r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b',  # MM/DD/YYYY, MM-DD-YYYY, etc.
        r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b',  # DD Month YYYY
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4}\b',  # Month DD, YYYY
        r'\b\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}\b',  # YYYY-MM-DD
        r'\b\d{1,2}(st|nd|rd|th)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b'  # 1st January 2025
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    
    return dates

def parse_date_string(date_str: str) -> Optional[date]:
    """Parse various date formats and return a date object"""
    date_formats = [
        "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d",
        "%B %d, %Y", "%b %d, %Y",
        "%d %B %Y", "%d %b %Y",
        "%m/%d/%y", "%m-%d-%y",
        "%d/%m/%y", "%d-%m-%y"
    ]
    
    # Clean the date string
    date_str = re.sub(r'(st|nd|rd|th)', '', date_str, flags=re.IGNORECASE)
    date_str = date_str.strip()
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            # Handle 2-digit years
            if parsed_date.year < 100:
                if parsed_date.year < 50:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                else:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
            return parsed_date
        except ValueError:
            continue
    
    return None

def extract_expiry_with_ai(text: str, prompt: str = None) -> Dict[str, Any]:
    """Use OpenAI to extract contract expiry information"""
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        if not prompt:
            prompt = """
            You are a legal AI assistant. Your task is to analyze the following contract text and extract expiry-related information.

            Focus on:
            1. The expiry date or termination date (phrases like "expires on", "valid until", "end date", etc.)
            2. The contract name or title if mentioned
            3. A short relevant text snippet where the expiry is found

            Return ONLY the following JSON format:
            {
            "expiry_date": "YYYY-MM-DD" or null,
            "contract_name": "extracted name" or null,
            "contract_title": "extracted title" or null,
            "confidence": float between 0.0 and 1.0,
            "extracted_text": "short relevant text snippet from the document"
                }

            Notes:
            - Use null if any field is not found.
            - Ensure "expiry_date" is strictly in "YYYY-MM-DD" format or null.
            - Do not include any extra explanation or commentary.
            - Return only valid JSON.

            Here is the contract text to analyze:
            """

        
        response = client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Document text:\n\n{text[:4000]}"}  # Limit text to avoid token limits
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        print("AI Raw Response:", result_text)


        
        # Try to parse as JSON
        import json
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # If not valid JSON, try to extract manually
            return {"error": "AI response was not valid JSON", "raw_response": result_text}
            
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return {"error": f"AI analysis failed: {str(e)}"}



def extract_expiry_with_rules(text: str) -> Dict[str, Any]:
    """Rule-based extraction as fallback"""
    expiry_keywords = [
        r'expires?\s+on\s+([^,\n\.]+)',
        r'expiry\s+date[:\s]+([^,\n\.]+)',
        r'termination\s+date[:\s]+([^,\n\.]+)',
        r'valid\s+until[:\s]+([^,\n\.]+)',
        r'validity\s+period[:\s]+([^,\n\.]+)',
        r'end\s+date[:\s]+([^,\n\.]+)',
        r'contract\s+ends?\s+on[:\s]+([^,\n\.]+)',
        r'shall\s+expire\s+on[:\s]+([^,\n\.]+)'
    ]
    
    title_keywords = [
        r'contract\s+title[:\s]+([^\n\.]+)',
        r'agreement\s+title[:\s]+([^\n\.]+)',
        r'this\s+([^,\n\.]*(?:agreement|contract)[^,\n\.]*)',
        r'^([^,\n\.]*(?:agreement|contract)[^,\n\.]*)',
    ]
    
    extracted_dates = []
    extracted_titles = []
    
    # Look for expiry dates
    for pattern in expiry_keywords:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            parsed_date = parse_date_string(match.strip())
            if parsed_date:
                extracted_dates.append({
                    'date': parsed_date,
                    'text': match.strip(),
                    'confidence': 0.8
                })
    
    # Look for contract titles
    for pattern in title_keywords:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        extracted_titles.extend([match.strip() for match in matches if match.strip()])
    
    # Find the most likely expiry date (closest future date)
    today = date.today()
    future_dates = [d for d in extracted_dates if d['date'] >= today]
    
    if future_dates:
        # Sort by date and take the nearest future date
        future_dates.sort(key=lambda x: (x['date'], -x['confidence']))
        best_date = future_dates[0]
        
        return {
            'expiry_date': best_date['date'].isoformat(),
            'contract_name': extracted_titles[0] if extracted_titles else None,
            'contract_title': extracted_titles[0] if extracted_titles else None,
            'confidence': best_date['confidence'],
            'extracted_text': best_date['text']
        }
    
    return {
        'expiry_date': None,
        'contract_name': extracted_titles[0] if extracted_titles else None,
        'contract_title': extracted_titles[0] if extracted_titles else None,
        'confidence': 0.0,
        'extracted_text': None
    }
