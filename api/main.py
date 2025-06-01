from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt, JWTError
from typing import List, Optional, Dict
import os
from datetime import datetime, timedelta
from faker import Faker
import random
from pydantic import BaseModel
import requests

app = FastAPI()
security = HTTPBearer(auto_error=False)  # Set auto_error to False to handle errors manually
fake = Faker()

# In-memory storage for reports
reports_storage: Dict[str, 'Report'] = {}

# Keycloak settings from environment variables
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "reports-api")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class Report(BaseModel):
    id: str
    date: str
    patient_name: str
    doctor_name: str
    type_of_prosthesis: str
    status: str
    user_id: str

class ReportRequest(BaseModel):
    patient_name: str
    type_of_prosthesis: Optional[str] = None

def generate_report(user_id: str) -> Report:
    """Generate a random report"""
    prosthesis_types = [
        "Full Denture",
        "Partial Denture",
        "Fixed Bridge",
        "Dental Implant",
        "All-on-4 Implants",
        "Dental Crown",
        "Implant-Supported Bridge"
    ]
    
    return Report(
        id=fake.uuid4(),
        date=datetime.now().strftime('%Y-%m-%d'),
        patient_name=fake.name(),
        doctor_name=f"Dr. {fake.name()}",
        type_of_prosthesis=random.choice(prosthesis_types),
        status="completed",
        user_id=user_id
    )

def get_token_public_key():
    try:
        r = requests.get(f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}")
        r.raise_for_status()
        return r.json()['public_key']
    except Exception as e:
        print(f"Error fetching public key: {e}")
        return None

async def verify_token(request: Request, credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    if not credentials:
        # Check if Authorization header exists
        if "Authorization" not in request.headers:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # If header exists but is invalid format
        auth_header = request.headers["Authorization"]
        scheme, _ = get_authorization_scheme_param(auth_header)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        raise HTTPException(
            status_code=401,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        # Fetch public key from Keycloak
        public_key = get_token_public_key()
        
        if not public_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify the token
        try:
            decoded_token = jwt.decode(
                token,
                f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----",
                algorithms=["RS256"],
                audience="account"
            )
        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid authentication credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user has the required role
        realm_access = decoded_token.get('realm_access', {})
        roles = realm_access.get('roles', [])
        
        if 'prothetic_user' not in roles:
            raise HTTPException(
                status_code=403,
                detail="Access denied. User must have prothetic_user role.",
            )
            
        return decoded_token
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/api/reports", response_model=Report)
async def create_report(
    request: Request,
    token: dict = Depends(verify_token)
):
    """Generate a new report when user clicks download"""
    user_id = token.get('sub', 'unknown')  # Get user ID from token
    report = generate_report(user_id)
    reports_storage[report.id] = report
    return report

@app.get("/api/reports", response_model=List[Report])
async def get_reports(
    request: Request,
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    token: dict = Depends(verify_token)
):
    """Get list of reports generated by the user"""
    user_id = token.get('sub', 'unknown')
    user_reports = [
        report for report in reports_storage.values()
        if report.user_id == user_id
    ]
    
    # Filter by status if provided
    if status:
        user_reports = [r for r in user_reports if r.status == status]
    
    # Basic pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_reports = user_reports[start_idx:end_idx]
    
    return paginated_reports

@app.get("/api/reports/{report_id}", response_model=Report)
async def get_report(
    request: Request,
    report_id: str,
    token: dict = Depends(verify_token)
):
    """Get a specific report by ID"""
    user_id = token.get('sub', 'unknown')
    report = reports_storage.get(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Ensure user can only access their own reports
    if report.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return report 