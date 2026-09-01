from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from src.adapters.allure.service import get_apis_from_allure_report

router = APIRouter(prefix="/allure", tags=["allure"])


@router.post("/reports")
async def upload_allure_report(file: UploadFile) -> list[dict]:
    """Upload an archive and extract it into a temporary directory.

    :param file: The uploaded file, must be a zip archive.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # 使用临时目录上下文，接口返回后自动清理。
    try:
        with tempfile.TemporaryDirectory(prefix="allure_") as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)

            # 将上传内容写入临时目录。
            upload_path = tmp_dir / file.filename
            try:
                with upload_path.open("wb") as f:
                    while chunk := await file.read(1024 * 1024):
                        f.write(chunk)
            except Exception as exc:
                raise HTTPException(
                    status_code=500, detail=f"Failed to save upload: {exc}"
                )
            finally:
                await file.close()

            # 解压（若为 zip），否则报错。
            try:
                if zipfile.is_zipfile(upload_path):
                    with zipfile.ZipFile(upload_path, "r") as zf:
                        zf.extractall(tmp_dir)
            except zipfile.BadZipFile:
                # 非合法 zip，报错。
                raise HTTPException(status_code=400, detail="Invalid zip file")
            except Exception as exc:
                raise HTTPException(
                    status_code=500, detail=f"Failed to extract archive: {exc}"
                )

            # 定位 Allure 报告根目录（包含 data/test-cases）。
            def find_report_root(base: Path) -> Path | None:
                candidate = base / "data" / "test-cases"
                if candidate.exists() and candidate.is_dir():
                    return base
                for child in base.iterdir():
                    if child.is_dir():
                        c2 = child / "data" / "test-cases"
                        if c2.exists() and c2.is_dir():
                            return child
                return None

            report_root = find_report_root(tmp_dir)
            if not report_root:
                raise HTTPException(
                    status_code=400, detail="Invalid Allure report content"
                )

            try:
                paths = get_apis_from_allure_report(report_root)
            except Exception as exc:
                raise HTTPException(
                    status_code=500, detail=f"Failed to parse report: {exc}"
                )

            return [{"path": p} for p in paths]
    except HTTPException:
        # 透传上面抛出的 HTTPException。
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")
