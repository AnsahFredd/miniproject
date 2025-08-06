# def serialize_document(document) -> dict:
#     return {
#         "id": str(document.id),
#         "user_id": str(document.user_id),
#         "upload_date": document.upload_date,
#         "filename": document.filename,
#         "file_type": document.file_type,
#         "content": document.content if hasattr(document, "content") else None,
#         "summary": document.summary if hasattr(document, "summary") else None,
#     }
