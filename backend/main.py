from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import jwt
import secrets
from pydantic import BaseModel, EmailStr
import os
import sys

# Import database components - these are lazy and won't fail until used
try:
    from database import SessionLocal, engine, Base
    from models import ProjectRequest, User
except Exception as e:
    print(f"⚠️ Warning: Database import failed: {e}", file=sys.stderr, flush=True)
    # Create dummy objects to allow app to start
    SessionLocal = None
    engine = None
    Base = None
    ProjectRequest = None
    User = None

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
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not available")
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
    """Initialize database on startup - non-blocking, app will start even if DB fails"""
    print("🚀 Starting application...", file=sys.stdout, flush=True)
    
    # Check if database components are available
    if engine is None or Base is None:
        print("⚠️ Database not available - app will start in limited mode", file=sys.stderr, flush=True)
        print("✅ Application started (database disabled)", file=sys.stdout, flush=True)
        return
    
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
        
        # Ensure database tables exist (non-blocking)
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created/verified", file=sys.stdout, flush=True)
        except Exception as db_error:
            print(f"⚠️ Database initialization error: {db_error}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
            # Continue anyway - app can still start
        
        # Initialize admin user (non-blocking)
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
        print("✅ Application started (with database warnings)", file=sys.stdout, flush=True)

# API status endpoint (for API clients)
@app.get("/api/status")
async def api_status():
    return {
        "message": "Resume Backend API",
        "docs": "/docs",
        "status": "running",
        "version": "1.0.0"
    }

# Serve frontend HTML files
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main index.html page"""
    # Try current directory first (where files are copied during build)
    base_dir = os.path.dirname(__file__)
    index_path = os.path.join(base_dir, "index.html")
    
    # Fallback to parent directory
    if not os.path.exists(index_path):
        index_path = os.path.join(os.path.dirname(base_dir), "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback message
    return HTMLResponse("""
    <html>
    <head><title>Resume API</title></head>
    <body>
        <h1>Resume Backend API</h1>
        <p>Status: Running</p>
        <p><a href="/docs">API Documentation</a></p>
        <p>Frontend files not found. Please ensure index.html is accessible.</p>
    </body>
    </html>
    """)

@app.get("/portfolio.html", response_class=HTMLResponse)
async def serve_portfolio():
    """Serve the portfolio page"""
    base_dir = os.path.dirname(__file__)
    portfolio_path = os.path.join(base_dir, "portfolio.html")
    if not os.path.exists(portfolio_path):
        portfolio_path = os.path.join(os.path.dirname(base_dir), "portfolio.html")
    if os.path.exists(portfolio_path):
        return FileResponse(portfolio_path)
    raise HTTPException(status_code=404, detail="Portfolio page not found")

@app.get("/admin.html", response_class=HTMLResponse)
async def serve_admin():
    """Serve the admin page"""
    base_dir = os.path.dirname(__file__)
    admin_path = os.path.join(base_dir, "admin.html")
    if not os.path.exists(admin_path):
        admin_path = os.path.join(os.path.dirname(base_dir), "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="Admin page not found")

# Serve CSS files
@app.get("/styles.css")
async def serve_styles():
    """Serve the main stylesheet"""
    base_dir = os.path.dirname(__file__)
    styles_path = os.path.join(base_dir, "styles.css")
    if not os.path.exists(styles_path):
        styles_path = os.path.join(os.path.dirname(base_dir), "styles.css")
    if os.path.exists(styles_path):
        return FileResponse(styles_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="Stylesheet not found")

@app.get("/portfolio.css")
async def serve_portfolio_css():
    """Serve the portfolio stylesheet"""
    base_dir = os.path.dirname(__file__)
    css_path = os.path.join(base_dir, "portfolio.css")
    if not os.path.exists(css_path):
        css_path = os.path.join(os.path.dirname(base_dir), "portfolio.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="Portfolio stylesheet not found")

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

