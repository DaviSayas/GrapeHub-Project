"""Local photo storage helper with validation."""
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CT = {"image/jpeg", "image/png", "image/webp"}


def _upload_root() -> Path:
    root = Path(settings.UPLOAD_DIR) / "wines"
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_wine_photo(file: UploadFile, wine_id: int, kind: str) -> str:
    """
    Validate and save an uploaded image. Returns the public path (/uploads/wines/..).
    kind: 'bottle' | 'label'
    Raises HTTPException on invalid type / size.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de ficheiro inválido. Permitidos: {', '.join(sorted(ALLOWED_EXT))}",
        )
    if file.content_type and file.content_type not in ALLOWED_CT:
        raise HTTPException(status_code=400, detail="Content-type de imagem inválido")

    data = file.file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Ficheiro demasiado grande (máx {settings.MAX_UPLOAD_MB} MB)",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Ficheiro vazio")

    fname = f"wine{wine_id}_{kind}_{uuid.uuid4().hex[:8]}{ext}"
    dest = _upload_root() / fname
    with open(dest, "wb") as f:
        f.write(data)

    return f"/uploads/wines/{fname}"


def delete_photo(public_path: str | None) -> None:
    """Best-effort delete of a previously stored photo."""
    if not public_path:
        return
    try:
        rel = public_path.lstrip("/")
        # public path is /uploads/wines/<file>; map to settings.UPLOAD_DIR
        fname = os.path.basename(rel)
        target = Path(settings.UPLOAD_DIR) / "wines" / fname
        if target.exists():
            target.unlink()
    except OSError:
        pass
