from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .database import DATA_DIR


ATTACHMENT_ROOT = Path(os.getenv("ATTACHMENT_ROOT", str(DATA_DIR / "attachments"))).resolve()
MAX_ATTACHMENT_BYTES = int(os.getenv("MAX_ATTACHMENT_BYTES", str(20 * 1024 * 1024)))
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _matches_signature(mime_type: str, content: bytes) -> bool:
    if mime_type == "application/pdf":
        return content.startswith(b"%PDF-")
    if mime_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if mime_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if mime_type == "image/webp":
        return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return False


async def store_upload(upload: UploadFile, kind: str) -> dict[str, object]:
    mime_type = (upload.content_type or "").lower()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            415,
            detail={"code": "unsupported_file_type", "message": f"Allowed types: {', '.join(sorted(ALLOWED_MIME_TYPES))}"},
        )
    content = await upload.read(MAX_ATTACHMENT_BYTES + 1)
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(413, detail={"code": "attachment_too_large", "message": "Attachment exceeds 20 MB"})
    if not _matches_signature(mime_type, content):
        raise HTTPException(415, detail={"code": "file_signature_mismatch", "message": "File content does not match its declared type"})
    digest = hashlib.sha256(content).hexdigest()
    relative = Path(kind) / digest[:2] / f"{uuid.uuid4().hex}{ALLOWED_MIME_TYPES[mime_type]}"
    destination = (ATTACHMENT_ROOT / relative).resolve()
    if ATTACHMENT_ROOT not in destination.parents:
        raise HTTPException(400, detail={"code": "invalid_storage_path", "message": "Invalid attachment path"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(destination)
    return {
        "local_path": relative.as_posix(),
        "original_filename": Path(upload.filename or "attachment").name,
        "mime_type": mime_type,
        "size_bytes": len(content),
        "sha256": digest,
        "absolute_path": destination,
    }


def resolve_attachment(relative_path: str) -> Path:
    path = (ATTACHMENT_ROOT / relative_path).resolve()
    if ATTACHMENT_ROOT not in path.parents or not path.is_file():
        raise HTTPException(404, detail={"code": "attachment_not_found", "message": "Attachment file not found"})
    return path


def remove_attachment(relative_path: str | None) -> None:
    if not relative_path:
        return
    try:
        resolve_attachment(relative_path).unlink(missing_ok=True)
    except HTTPException:
        return
