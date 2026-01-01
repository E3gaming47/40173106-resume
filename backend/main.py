from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import jwt
import secrets
from pydantic import BaseModel, EmailStr
from database import SessionLocal, engine, Base
from models import ProjectRequest, User
import os
import sys

# Database tables will be created on startup event

app = FastAPI(
    title="Resume Backend API",
    description="Backend API for interactive resume with project requests and admin panel",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.broadcast_count()
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Broadcast count asynchronously
        import asyncio
        asyncio.create_task(self.broadcast_count())
    
    async def broadcast_count(self):
        count = len(self.active_connections)
        message = {"type": "online_count", "count": count}
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class ProjectRequestCreate(BaseModel):
    name: str
    email: EmailStr
    project_description: str
    budget: Optional[str] = None
    timeline: Optional[str] = None
    project_type: Optional[str] = None

class ProjectRequestResponse(BaseModel):
    id: int
    name: str
    email: str
    project_description: str
    budget: Optional[str]
    timeline: Optional[str]
    project_type: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProjectRequestUpdate(BaseModel):
    status: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Authentication
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Initialize admin user if not exists
def init_admin_user(db: Session):
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        # Default password: admin123 (should be changed in production)
        import hashlib
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        admin = User(username="admin", password_hash=password_hash)
        db.add(admin)
        db.commit()
        print("Admin user created: username=admin, password=admin123")

# Routes
@app.on_event("startup")
async def startup_event():
    try:
        from database import SQLALCHEMY_DATABASE_URL
        
        # Ensure /tmp directory exists (only for SQLite in containers)
        if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
            try:
                if not os.path.exists("/tmp"):
                    os.makedirs("/tmp", exist_ok=True)
                # Verify /tmp is writable
                test_file = "/tmp/.test_write"
                try:
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                except:
                    print("⚠️ /tmp is not writable, using current directory", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"⚠️ Could not create /tmp: {e}", file=sys.stderr, flush=True)
        
        # Ensure database tables exist
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created/verified", file=sys.stdout, flush=True)
        except Exception as db_error:
            print(f"⚠️ Database initialization error: {db_error}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            # Continue anyway - app can still start
        
        # Initialize admin user
        try:
            db = SessionLocal()
            try:
                init_admin_user(db)
            finally:
                db.close()
        except Exception as user_error:
            print(f"⚠️ Admin user initialization error: {user_error}", file=sys.stderr, flush=True)
        
        db_type = "MSSQL" if "mssql" in SQLALCHEMY_DATABASE_URL.lower() else "SQLite"
        print(f"✅ Application started successfully with {db_type} database", file=sys.stdout, flush=True)
    except Exception as e:
        print(f"⚠️ Startup warning: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Don't fail the app, just log the error
        # App will still start but database operations might fail
        print("⚠️ Application starting with limited functionality", file=sys.stdout, flush=True)

@app.get("/")
async def root():
    return {
        "message": "Resume Backend API",
        "docs": "/docs",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "resume-api"}

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    import hashlib
    password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
    user = db.query(User).filter(
        User.username == login_data.username,
        User.password_hash == password_hash
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/project-requests", response_model=ProjectRequestResponse)
async def create_project_request(request: ProjectRequestCreate, db: Session = Depends(get_db)):
    db_request = ProjectRequest(
        name=request.name,
        email=request.email,
        project_description=request.project_description,
        budget=request.budget,
        timeline=request.timeline,
        project_type=request.project_type,
        status="pending"
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/api/project-requests", response_model=List[ProjectRequestResponse])
async def get_project_requests(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    requests = db.query(ProjectRequest).offset(skip).limit(limit).all()
    return requests

@app.get("/api/project-requests/{request_id}", response_model=ProjectRequestResponse)
async def get_project_request(
    request_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Project request not found")
    return request

@app.patch("/api/project-requests/{request_id}", response_model=ProjectRequestResponse)
async def update_project_request(
    request_id: int,
    request_update: ProjectRequestUpdate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    if request_update.status:
        db_request.status = request_update.status
    db.commit()
    db.refresh(db_request)
    return db_request

@app.delete("/api/project-requests/{request_id}")
async def delete_project_request(
    request_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    db.delete(db_request)
    db.commit()
    return {"message": "Project request deleted successfully"}

@app.websocket("/ws/online-users")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    # لیارا از پورت 80 استفاده می‌کند
    port = int(os.getenv("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)

