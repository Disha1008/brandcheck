from pathlib import Path
from uuid import uuid4
from hashlib import sha256
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PIL import Image, ImageChops, ImageStat, UnidentifiedImageError
from auth import get_current_user, require_roles
from database import get_db
from models import BrandAsset, BrandColor, User
from services import log
from models import Draft

router = APIRouter(prefix="/assets", tags=["approved visual assets"])


class BrandColorIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    hex_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
ASSET_DIR = Path(__file__).resolve().parents[1] / "uploads" / "assets"
ASSET_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 5 * 1024 * 1024
ALLOWED = {"image/png", "image/jpeg", "image/webp"}


def serialize(a):
    return {"id":a.id,"name":a.name,"media_type":a.media_type,"sha256":a.sha256,"width":a.width,
            "height":a.height,"average_color":a.average_color,"created_at":a.created_at.isoformat(),
            "uploaded_by":a.uploaded_by}


def read_image(raw: bytes):
    try:
        im = Image.open(BytesIO(raw))
        im.verify()
        im = Image.open(BytesIO(raw)).convert("RGB")
        if im.width > 8000 or im.height > 8000:
            raise HTTPException(413, "Image dimensions must be 8000 × 8000 pixels or smaller")
        stat = ImageStat.Stat(im.resize((1, 1)))
        color = "#%02X%02X%02X" % tuple(round(x) for x in stat.mean[:3])
        return im, color
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(415, "This file is not a supported readable image")


def perceptual_hash(im):
    im = im.convert("L").resize((8, 8))
    values = list(im.getdata()); avg = sum(values) / len(values)
    return sum(1 << i for i, value in enumerate(values) if value >= avg)


def hamming(a, b):
    return (a ^ b).bit_count()


def color_distance(hex_a, hex_b):
    try:
        a = tuple(int(hex_a[i:i+2], 16) for i in (1, 3, 5))
        b = tuple(int(hex_b[i:i+2], 16) for i in (1, 3, 5))
        return round(sum((x-y)**2 for x, y in zip(a, b)) ** 0.5, 1)
    except Exception:
        return 999.0


@router.get("/palette")
def list_palette(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [{"id":c.id,"name":c.name,"hex_color":c.hex_color,"created_at":c.created_at.isoformat()}
            for c in db.query(BrandColor).filter_by(org_id=user.org_id).order_by(BrandColor.name).all()]


@router.post("/palette", status_code=201)
def add_palette_color(data: BrandColorIn, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    color = BrandColor(org_id=user.org_id, name=data.name.strip(), hex_color=data.hex_color.upper())
    db.add(color); db.commit(); db.refresh(color)
    return {"id":color.id,"name":color.name,"hex_color":color.hex_color,"created_at":color.created_at.isoformat()}


@router.delete("/palette/{color_id}")
def delete_palette_color(color_id: int, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    color = db.query(BrandColor).filter_by(id=color_id, org_id=user.org_id).first()
    if not color: raise HTTPException(404, "Brand color not found")
    db.delete(color); db.commit()
    return {"deleted":color_id}


@router.get("")
def list_assets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [serialize(a) for a in db.query(BrandAsset).filter_by(org_id=user.org_id).order_by(BrandAsset.created_at.desc()).all()]


@router.post("", status_code=201)
async def add_asset(file: UploadFile = File(...), user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Use a PNG, JPEG or WebP image")
    raw = await file.read()
    if not raw or len(raw) > MAX_BYTES:
        raise HTTPException(413 if raw else 400, "Image must be between 1 byte and 5 MB")
    im, color = read_image(raw)
    storage = f"{uuid4().hex}{Path(file.filename or 'asset').suffix.lower()}"
    (ASSET_DIR / storage).write_bytes(raw)
    asset = BrandAsset(org_id=user.org_id, uploaded_by=user.id, name=(file.filename or "Approved asset")[:200],
        storage_name=storage, media_type=file.content_type, sha256=sha256(raw).hexdigest(),
        width=im.width, height=im.height, average_color=color)
    db.add(asset); db.commit(); db.refresh(asset)
    return serialize(asset)


@router.get("/{asset_id}/file")
def asset_file(asset_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    asset = db.query(BrandAsset).filter_by(id=asset_id, org_id=user.org_id).first()
    if not asset:
        raise HTTPException(404, "Asset not found")
    path = ASSET_DIR / asset.storage_name
    if not path.is_file():
        raise HTTPException(410, "Stored asset file is missing")
    return FileResponse(path, media_type=asset.media_type)


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    asset = db.query(BrandAsset).filter_by(id=asset_id, org_id=user.org_id).first()
    if not asset:
        raise HTTPException(404, "Asset not found")
    path = ASSET_DIR / asset.storage_name
    if path.is_file(): path.unlink()
    db.delete(asset); db.commit()
    return {"deleted":asset_id}


@router.post("/check")
async def check_asset(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Use a PNG, JPEG or WebP image")
    raw = await file.read()
    if not raw or len(raw) > MAX_BYTES:
        raise HTTPException(413 if raw else 400, "Image must be between 1 byte and 5 MB")
    im, color = read_image(raw)
    digest = sha256(raw).hexdigest()
    approved = db.query(BrandAsset).filter_by(org_id=user.org_id).all()
    palette = db.query(BrandColor).filter_by(org_id=user.org_id).all()
    palette_matches = sorted([{"id":c.id,"name":c.name,"hex_color":c.hex_color,
                               "distance":color_distance(color,c.hex_color)} for c in palette], key=lambda x:x["distance"])
    exact = next((a for a in approved if a.sha256 == digest), None)
    comparisons=[]
    target_hash = perceptual_hash(im)
    for asset in approved:
        path = ASSET_DIR / asset.storage_name
        if not path.is_file(): continue
        try:
            ref = Image.open(path).convert("RGB")
            distance = hamming(target_hash, perceptual_hash(ref))
            color_delta = color_distance(color, asset.average_color)
            comparisons.append((distance, color_delta, asset))
        except Exception:
            continue
    closest = sorted(comparisons, key=lambda x:(x[0], x[1]))[:3]
    if exact:
        status = "exact_match"
        message = "This image exactly matches an approved asset (same file hash)."
    elif closest and closest[0][0] <= 8 and closest[0][1] <= 65:
        status = "visually_similar"
        message = "This image resembles an approved asset by simple thumbnail structure and average color, but it is not an exact match. A human must verify that it is an allowed variant."
    else:
        status = "not_in_library"
        message = "No matching approved asset was found. This does not prove the image is off-brand; add it to the approved library or ask a reviewer to verify it."
    return {"filename":file.filename,"status":status,"message":message,"width":im.width,"height":im.height,
            "average_color":color,"approved_asset_count":len(approved),
            "palette_matches":palette_matches[:3],
            "palette_status":"near_palette_color" if palette_matches and palette_matches[0]["distance"] <= 65 else ("outside_palette_range" if palette_matches else "no_palette_configured"),
            "matches":[{"asset":serialize(a),"thumbnail_distance":d,"average_color_distance":cd,"exact":a.sha256==digest} for d,cd,a in closest]}
