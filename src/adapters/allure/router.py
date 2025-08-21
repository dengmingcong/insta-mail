from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

router = APIRouter(prefix="/allure", tags=["allure"])


@router.post("/reports")
async def upload_allure_report(file: UploadFile) -> dict:
    """Upload an archive and extract it into a temporary directory.

    :param file: The uploaded file, must be a zip archive.
    """
    # Basic content-type check (optional)
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Create a temp dir to extract
    try:
        tmp_dir = Path(tempfile.mkdtemp(prefix="allure_"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create temp dir: {exc}")

    # Save uploaded file to a temp path
    upload_path = tmp_dir / file.filename
    try:
        with upload_path.open("wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc}")
    finally:
        await file.close()

    # Try unzip if it's a zip, otherwise just leave as is
    try:
        if zipfile.is_zipfile(upload_path):
            with zipfile.ZipFile(upload_path, "r") as zf:
                zf.extractall(tmp_dir)
    except zipfile.BadZipFile:
        # Not a valid zip, ignore extraction
        pass
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to extract archive: {exc}")

    # TODO: parse extracted allure report and return interface list
    # Placeholder return to satisfy current frontend contract
    return {"message": "uploaded", "tmp_dir": str(tmp_dir)}
