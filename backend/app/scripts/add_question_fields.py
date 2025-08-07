# scripts/add_questions_field.py
"""
Migration script to add questions_asked field to existing documents
Run this once to update your existing documents.
"""

import asyncio
from app.models.document import AcceptedDocument
from app.database.mongo import connect_to_mongo  # ✅ FIXED

async def add_questions_field():
    """
    Add questions_asked field to existing documents that don't have it
    """
    await connect_to_mongo()  # ✅ FIXED
    
    updated_count = 0
    total_count = 0
    
    print("Starting migration to add questions_asked field...")
    
    async for doc in AcceptedDocument.find():
        total_count += 1
        
        if not hasattr(doc, 'questions_asked') or doc.questions_asked is None:
            doc.questions_asked = []
            await doc.save()
            updated_count += 1
            print(f"✅ Updated document: {doc.filename}")
        else:
            print(f"⏭️  Document already has questions_asked field: {doc.filename}")
    
    print(f"\nMigration completed:")
    print(f"Total documents processed: {total_count}")
    print(f"Documents updated: {updated_count}")
    print(f"Documents already had field: {total_count - updated_count}")

if __name__ == "__main__":
    asyncio.run(add_questions_field())
