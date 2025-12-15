"""File upload and management endpoints."""
import hashlib
import logging
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, status, Depends

from app.core.config import settings
from app.core.exceptions import InvalidFileFormatError, FileTooLargeError, DataIngestionError
from app.core.security import check_file_extension, sanitize_filename
# from app.api.dependencies import SessionManagerDep
from app.api.dependencies import get_session_manager
from app.services.session_manager2 import SessionManager
from app.services.ingest import create_data_frame
from app.models.response_data import DataResponses

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_files(
        files: List[UploadFile] = File(..., description="Files to upload (CSV, Excel, etc.)"),
        session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Upload one or multiple data files.

    Supported formats: CSV, DSV, TSV, XLSX, XLS, JSON
    Maximum size per file: 100MB (configurable)

    Returns:
        - session_id: Unique identifier for this data session
        - data_responses: Metadata about uploaded tables
    """
    logger.info(f"Received {len(files)} file(s) for upload")

    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )

    # Validate files
    for file in files:
        # Sanitize filename
        original_filename = file.filename
        file.filename = sanitize_filename(file.filename)

        if original_filename != file.filename:
            logger.warning(f"Filename sanitized: {original_filename} -> {file.filename}")

        # Check extension
        if not check_file_extension(file.filename):
            raise InvalidFileFormatError(
                filename=file.filename,
                expected_formats=settings.allowed_extensions
            )

        # Check size (read content to verify)
        content = await file.read()
        if len(content) > settings.max_upload_size:
            raise FileTooLargeError(
                filename=file.filename,
                size=len(content),
                max_size=settings.max_upload_size
            )

        # Reset file pointer
        await file.seek(0)

        logger.info(f"File validated: {file.filename} ({len(content)} bytes)")

    try:
        # Process files
        logger.info("Processing files to dataframes...")
        table_data, dataframes = await create_data_frame(files=files)
        logger.info(f"Created {len(dataframes)} dataframe(s)")

        # Generate session ID from first file content
        first_file_content = await files[0].read()
        session_id = hashlib.md5(first_file_content).hexdigest()
        logger.info(f"Generated session ID: {session_id}")

        # Store in session manager
        session_manager.create_session(
            session_id=session_id,
            dataframes=dataframes,
            table_data=table_data,
            source_type="file"
        )
        logger.info(f"Session created successfully: {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "data_responses": DataResponses(
                message=f"Successfully uploaded {len(files)} file(s)",
                total_tables=len(table_data),
                data_tables=table_data
            )
        }

    except Exception as e:
        logger.exception(f"Failed to process files: {e}")
        raise DataIngestionError(
            message="Failed to process uploaded files",
            details={"error": str(e), "files": [f.filename for f in files]}
        )

@router.get("/formats", status_code=status.HTTP_200_OK)
async def get_supported_formats():
    """
    Get list of supported file formats.

    Returns information about file upload limits and supported formats.
    """
    return {
        "supported_formats": settings.allowed_extensions,
        "max_file_size_bytes": settings.max_upload_size,
        "max_file_size_mb": settings.max_upload_size / (1024 * 1024),
        "examples": {
            "csv": "Comma-separated values file",
            "xlsx": "Excel 2007+ spreadsheet",
            "xls": "Excel 97-2003 spreadsheet",
            "json": "JSON data file"
        }
    }


@router.get("/validate", status_code=status.HTTP_200_OK)
async def validate_file_format(filename: str):
    """
    Validate if a filename has a supported format.

    Args:
        filename: Name of the file to validate

    Returns:
        validation result with details
    """
    is_valid = check_file_extension(filename)

    if is_valid:
        extension = filename.rsplit('.', 1)[1].lower()
        return {
            "valid": True,
            "filename": filename,
            "extension": extension,
            "message": f"File format '{extension}' is supported"
        }
    else:
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else "unknown"
        return {
            "valid": False,
            "filename": filename,
            "extension": extension,
            "message": f"File format '{extension}' is not supported",
            "supported_formats": settings.allowed_extensions
        }