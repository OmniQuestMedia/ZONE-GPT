import os
import hashlib
import csv
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.audit import log_audit_event

app = FastAPI()

# Configure CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
DATASETS_DIR = os.getenv("DATASETS_DIR", "/datasets")

@app.post("/ingest/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV dataset file.

    Validates:
    - File must be a .csv file
    - File must be UTF-8 encoded
    - File must have a header row
    - File size must not exceed MAX_FILE_SIZE

    Returns:
    - File path
    - SHA256 checksum
    """
    # Validate file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are allowed")

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )

    # Validate UTF-8 encoding
    try:
        decoded_content = content.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400, detail="File must be UTF-8 encoded"
        ) from exc

    # Validate header row exists
    lines = decoded_content.strip().split('\n')
    if len(lines) < 1:
        raise HTTPException(
            status_code=400, detail="File must contain at least a header row"
        )

    # Validate CSV format and header
    try:
        csv_reader = csv.reader([lines[0]])
        header = next(csv_reader)
        if not header or all(not field.strip() for field in header):
            raise HTTPException(
                status_code=400, detail="File must have a valid header row"
            )
    except (csv.Error, StopIteration) as exc:
        raise HTTPException(status_code=400, detail="Invalid CSV format") from exc

    # Compute SHA256 checksum
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Extract name from filename (without extension)
    file_name = Path(file.filename).stem

    # Create directory structure /datasets/<name>/
    dataset_path = Path(DATASETS_DIR) / file_name
    dataset_path.mkdir(parents=True, exist_ok=True)

    # Store file as <version>.csv (using "v1" as placeholder)
    version = "v1"
    file_path = dataset_path / f"{version}.csv"

    # Write file to disk
    with open(file_path, 'wb') as f:
        f.write(content)

    # Emit audit event
    log_audit_event(
        event_type="dataset.ingest",
        details={
            "filename": file.filename,
            "size": len(content),
            "checksum": sha256_hash,
            "path": str(file_path)
        }
    )

    return {
        "message": "File uploaded successfully",
        "path": str(file_path),
        "checksum": sha256_hash,
        "size": len(content)
    }
