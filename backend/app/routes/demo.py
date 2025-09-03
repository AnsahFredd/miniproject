from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import logging
from typing import Optional
from app.services.demo_service import process_demo_document, get_available_demos

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/")
async def demo_processing(
    document_type: Optional[str] = Query(default="employment_contract", description="Type of demo document to process")
):
    """
    Run a demo using the dedicated demo service (no database persistence).
    
    Available document types:
    - employment_contract: Sample employment agreement
    - service_agreement: Sample service agreement  
    - lease_agreement: Sample lease agreement
    """
    try:
        logger.info(f"[DEMO ENDPOINT] Processing demo for document_type: {document_type}")
        
        # Use the dedicated demo service
        result = await process_demo_document(document_type)
        
        logger.info(f"[DEMO ENDPOINT] Demo completed successfully for {document_type}")
        return result
        
    except Exception as e:
        logger.error(f"[DEMO ENDPOINT ERROR] Failed to process demo: {str(e)}")
        return {
            "title": "Demo: Processing Error",
            "summary": f"An error occurred during demo processing: {str(e)}",
            "clauses": [],
            "validation": {},
            "classification": {},
            "tags": ["demo_error"],
            "processing_success": False,
            "rejection_reason": f"Demo system error: {str(e)}",
            "note": "Please try again or contact support if the issue persists"
        }

@router.get("/mock")
async def mock_demo_endpoint():
    """
    Fallback mock demo endpoint with static data for development/testing.
    Returns a pre-defined successful contract validation result.
    """
    try:
        logger.info("[MOCK DEMO] Returning static demo data")
        
        return {
            "title": "Mock Demo: Employment Contract Analysis",
            "processing_success": True,
            "summary": "This is a comprehensive employment agreement between TechCorp Inc. and a software engineer. The contract includes standard employment terms including salary, benefits, confidentiality clauses, and termination conditions. The agreement demonstrates typical corporate employment structure with competitive compensation and standard legal protections for both employer and employee.",
            "validation": {
                "contract_type": "employment_agreement",
                "confidence": 0.92,
                "is_valid": True
            },
            "classification": {
                "document_type": "employment_contract",
                "legal_domain": "employment_law",
                "urgency": "medium",
                "extracted_entities": [
                    {"type": "ORG", "text": "TechCorp Inc."},
                    {"type": "PERSON", "text": "Software Engineer"},
                    {"type": "MONEY", "text": "$85,000"},
                    {"type": "DATE", "text": "January 1, 2024"}
                ]
            },
            "tags": [
                "employment_contract",
                "tech_industry", 
                "validated_contract",
                "high_confidence",
                "has_compensation"
            ],
            "clauses": [
                "Position: Software Engineer with responsibilities in web development",
                "Compensation: Annual salary of $85,000 with performance reviews",
                "Benefits: Health insurance, dental coverage, and 401k matching",
                "Confidentiality: Protection of company trade secrets and IP",
                "Termination: 2 weeks notice required from either party"
            ],
            "note": "Mock demo data for testing purposes",
            "demo_metadata": {
                "document_type": "mock",
                "is_demo": True,
                "is_mock": True
            }
        }
        
    except Exception as e:
        logger.error(f"[MOCK DEMO ERROR] {str(e)}")
        return {
            "title": "Mock Demo: Error",
            "processing_success": False,
            "rejection_reason": f"Mock demo error: {str(e)}",
            "validation": {},
            "classification": {},
            "tags": [],
            "clauses": []
        }

@router.get("/types")
async def get_demo_types():
    """
    Get available demo document types and their descriptions.
    """
    try:
        available_demos = get_available_demos()
        return {
            "available_demos": available_demos,
            "default": "employment_contract",
            "total_count": len(available_demos)
        }
    except Exception as e:
        logger.error(f"Error fetching demo types: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch available demo types")

@router.get("/{document_type}")
async def demo_by_type(document_type: str):
    """
    Process a specific demo document type directly via URL path.
    """
    return await demo_processing(document_type=document_type)