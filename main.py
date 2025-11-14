import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Any, Dict

from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

from database import db
from schemas import Project, BlogPost, TechItem
from bson import ObjectId

# ---------- Helpers ----------

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TOKEN_EXPIRE_MINUTES = 60 * 8

security = HTTPBearer()


def create_token(payload: dict) -> str:
    to_encode = payload.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if data.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return data
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ObjectId conversion
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    doc = dict(doc)
    _id = doc.pop("_id", None)
    if _id is not None:
        doc["id"] = str(_id)
    # Convert datetimes
    for k, v in doc.items():
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


# ---------- FastAPI app ----------
app = FastAPI(title="Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Portfolio API running"}


# ---------- Auth ----------
class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    if payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token({"role": "admin"})
    return TokenResponse(access_token=token)


# ---------- CRUD Utilities ----------

def ensure_db():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available. Configure DATABASE_URL and DATABASE_NAME.")


def collection(name: str):
    ensure_db()
    return db[name]


# ---------- Projects ----------
@app.get("/projects", response_model=List[dict])
def list_projects(limit: Optional[int] = None):
    cur = collection("project").find({}).sort("created_at", -1)
    if limit:
        cur = cur.limit(limit)
    return [serialize_doc(d) for d in cur]


@app.get("/projects/slug/{slug}")
def get_project_by_slug(slug: str):
    doc = collection("project").find_one({"slug": slug})
    if not doc:
        raise HTTPException(404, detail="Project not found")
    return serialize_doc(doc)


@app.post("/projects", dependencies=[Depends(require_admin)])
def create_project(data: Project):
    now = datetime.now(timezone.utc)
    doc = data.model_dump()
    doc["created_at"] = now
    doc["updated_at"] = now
    res = collection("project").insert_one(doc)
    return {"id": str(res.inserted_id)}


@app.put("/projects/{id}", dependencies=[Depends(require_admin)])
def update_project(id: str, data: Project):
    now = datetime.now(timezone.utc)
    res = collection("project").update_one({"_id": ObjectId(id)}, {"$set": {**data.model_dump(), "updated_at": now}})
    if res.matched_count == 0:
        raise HTTPException(404, detail="Not found")
    return {"ok": True}


@app.delete("/projects/{id}", dependencies=[Depends(require_admin)])
def delete_project(id: str):
    res = collection("project").delete_one({"_id": ObjectId(id)})
    if res.deleted_count == 0:
        raise HTTPException(404, detail="Not found")
    return {"ok": True}


# ---------- Blog ----------
@app.get("/blog", response_model=List[dict])
def list_blog(limit: Optional[int] = None):
    cur = collection("blogpost").find({}).sort("created_at", -1)
    if limit:
        cur = cur.limit(limit)
    return [serialize_doc(d) for d in cur]


@app.get("/blog/slug/{slug}")
def get_post_by_slug(slug: str):
    doc = collection("blogpost").find_one({"slug": slug})
    if not doc:
        raise HTTPException(404, detail="Post not found")
    return serialize_doc(doc)


@app.post("/blog", dependencies=[Depends(require_admin)])
def create_post(data: BlogPost):
    now = datetime.now(timezone.utc)
    doc = data.model_dump()
    doc["created_at"] = now
    doc["updated_at"] = now
    res = collection("blogpost").insert_one(doc)
    return {"id": str(res.inserted_id)}


@app.put("/blog/{id}", dependencies=[Depends(require_admin)])
def update_post(id: str, data: BlogPost):
    now = datetime.now(timezone.utc)
    res = collection("blogpost").update_one({"_id": ObjectId(id)}, {"$set": {**data.model_dump(), "updated_at": now}})
    if res.matched_count == 0:
        raise HTTPException(404, detail="Not found")
    return {"ok": True}


@app.delete("/blog/{id}", dependencies=[Depends(require_admin)])
def delete_post(id: str):
    res = collection("blogpost").delete_one({"_id": ObjectId(id)})
    if res.deleted_count == 0:
        raise HTTPException(404, detail="Not found")
    return {"ok": True}


# ---------- Tech Stack ----------
@app.get("/tech", response_model=List[dict])
def list_tech():
    cur = collection("techitem").find({}).sort("name", 1)
    return [serialize_doc(d) for d in cur]


@app.post("/tech", dependencies=[Depends(require_admin)])
def create_tech(data: TechItem):
    now = datetime.now(timezone.utc)
    doc = data.model_dump()
    doc["created_at"] = now
    doc["updated_at"] = now
    res = collection("techitem").insert_one(doc)
    return {"id": str(res.inserted_id)}


@app.put("/tech/{id}", dependencies=[Depends(require_admin)])
def update_tech(id: str, data: TechItem):
    now = datetime.now(timezone.utc)
    res = collection("techitem").update_one({"_id": ObjectId(id)}, {"$set": {**data.model_dump(), "updated_at": now}})
    if res.matched_count == 0:
        raise HTTPException(404, detail="Not found")
    return {"ok": True}


@app.delete("/tech/{id}", dependencies=[Depends(require_admin)])
def delete_tech(id: str):
    res = collection("techitem").delete_one({"_id": ObjectId(id)})
    if res.deleted_count == 0:
        raise HTTPException(404, detail="Not found")
    return {"ok": True}


# ---------- Public home helpers ----------
@app.get("/home")
def home_data():
    projects = list(collection("project").find({}).sort("created_at", -1).limit(6))
    posts = list(collection("blogpost").find({}).sort("created_at", -1).limit(3))
    tech = list(collection("techitem").find({}).sort("name", 1))
    return {
        "projects": [serialize_doc(p) for p in projects],
        "posts": [serialize_doc(p) for p in posts],
        "tech": [serialize_doc(t) for t in tech],
    }


@app.get("/test")
def test_database():
    status_obj = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "connection_status": "Not Connected",
    }
    try:
        if db is not None:
            status_obj["database"] = "✅ Available"
            status_obj["connection_status"] = "Connected"
            status_obj["collections"] = db.list_collection_names()
        else:
            status_obj["database"] = "⚠️ Not configured"
    except Exception as e:
        status_obj["database"] = f"Error: {str(e)[:80]}"
    return status_obj


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
