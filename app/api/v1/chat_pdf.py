from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.db.mongo import sessions_collection
import PyPDF2
import io

router = APIRouter()

# this route for uploadinf the pdf files


@router.post("/sessions/{session_id}/upload-pdf")
async def upload_pdf(session_id: str, file: UploadFile = File(...)):
    """
    Upload and extract text from a PDF file for a session
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed")

    try:
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        await sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {
                "pdf": {
                    "filename": file.filename,
                    "content": text,
                    "uploaded_at": datetime.utcnow()
                }
            }},
            upsert=True
        )

        return {"message": "PDF uploaded successfully",
                "pages": len(pdf_reader.pages)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing PDF: {str(e)}")
