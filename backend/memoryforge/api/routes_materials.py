"""Material upload and processing routes."""

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form

from memoryforge.parser.material_processor import MaterialProcessor

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("")
def list_materials(request: Request, subject_id: int | None = None):
    repo = request.app.state.repo
    return repo.list_materials(subject_id=subject_id)


@router.post("", status_code=201)
async def upload_material(
    request: Request,
    subject_id: int = Form(...),
    file: UploadFile = File(...),
):
    repo = request.app.state.repo
    config = request.app.state.config

    config.uploads_dir.mkdir(parents=True, exist_ok=True)
    prefix = uuid.uuid4().hex
    dest = config.uploads_dir / f"{prefix}_{file.filename}"
    content = await file.read()
    dest.write_bytes(content)

    material_id = repo.create_material(
        subject_id=subject_id,
        filename=file.filename,
        file_path=str(dest),
        file_type=Path(file.filename).suffix.lstrip(".").lower(),
    )

    processor = MaterialProcessor(repo=repo, config=config)
    processor.light_parse(material_id)

    return repo.get_material(material_id)


@router.post("/{material_id}/parse-now")
async def parse_now(material_id: int, request: Request):
    repo = request.app.state.repo
    config = request.app.state.config

    material = repo.get_material(material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")

    processor = MaterialProcessor(repo=repo, config=config)
    ku_count = await processor.deep_parse(material_id)
    return {"material_id": material_id, "ku_count": ku_count}
