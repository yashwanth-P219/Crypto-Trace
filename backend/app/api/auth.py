import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.database.models import (
    User, UserRole, AuditLog, InvestigatorProfile,
    InvestigatorApprovalStatus, InvestigatorAvailabilityStatus
)
from app.database.schemas import (
    UserCreate, UserResponse, TokenResponse, LoginRequest,
    UserRegisterRequest
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (
        expires_delta or datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker

@router.post("/register", response_model=UserResponse)
def register(user_in: UserRegisterRequest, db: Session = Depends(get_db)):
    # Block public registration for privileged roles
    if user_in.role in [UserRole.ADMINISTRATOR, UserRole.SUPERVISOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative accounts cannot be self-registered. Please contact system administration."
        )

    # Check for existing username or email or phone
    query = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    )
    if user_in.phone_number:
        query = db.query(User).filter(
            (User.username == user_in.username) |
            (User.email == user_in.email) |
            (User.phone_number == user_in.phone_number)
        )
    existing = query.first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username, email, or mobile number is already registered"
        )

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        badge_number=user_in.badge_number,
        phone_number=user_in.phone_number,
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # If investigator, create pending profile
    if user.role == UserRole.INVESTIGATOR:
        profile = InvestigatorProfile(
            user_id=user.id,
            organization=user_in.organization or "Cyber Crime Cell",
            department=user_in.department or "Digital Forensics",
            experience_years=user_in.experience_years or 0,
            specialization=user_in.specialization or "Cryptocurrency Analytics",
            badge_id=user_in.badge_number,
            approval_status=InvestigatorApprovalStatus.PENDING,
            availability_status=InvestigatorAvailabilityStatus.OFFLINE
        )
        db.add(profile)
        db.commit()

    # Audit log
    log = AuditLog(
        user_id=user.id,
        username=user.username,
        action="USER_REGISTERED",
        metadata_json={
            "role": user.role.value,
            "is_pending_approval": user.role == UserRole.INVESTIGATOR
        }
    )
    db.add(log)
    db.commit()
    return user

@router.post("/login", response_model=TokenResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    # Support username, email, or phone number login
    user = db.query(User).filter(
        (User.username == login_req.username) |
        (User.email == login_req.username) |
        (User.phone_number == login_req.username)
    ).first()

    if not user or not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, email, or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )

    # Check investigator approval status if applicable
    approval_status = None
    if user.role == UserRole.INVESTIGATOR:
        prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == user.id).first()
        if prof:
            approval_status = prof.approval_status.value

    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})

    log = AuditLog(
        user_id=user.id,
        username=user.username,
        action="USER_LOGIN",
        metadata_json={"role": user.role.value, "approval_status": approval_status}
    )
    db.add(log)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "investigator_approval_status": approval_status
    }

@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        (User.username == form_data.username) |
        (User.email == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/seed-users")
def seed_default_users(db: Session = Depends(get_db)):
    """Seeds multi-role dynamic accounts for SIH evaluation"""
    default_users = [
        {
            "username": "investigator",
            "email": "investigator@cybercrime.gov.in",
            "password": "password123",
            "role": UserRole.INVESTIGATOR,
            "full_name": "Inspector Vikram Malhotra",
            "badge_number": "CYBER-INV-4412",
            "phone_number": "+919876543210",
            "profile": {
                "organization": "State Cyber Crime Wing",
                "department": "Cryptocurrency Intelligence Unit",
                "experience_years": 8,
                "specialization": "Ethereum & EVM Forensics, VASP Subpoenas",
                "approval_status": InvestigatorApprovalStatus.APPROVED,
                "availability_status": InvestigatorAvailabilityStatus.AVAILABLE
            }
        },
        {
            "username": "investigator2",
            "email": "priya.nair@cybercrime.gov.in",
            "password": "password123",
            "role": UserRole.INVESTIGATOR,
            "full_name": "Sub-Inspector Priya Nair",
            "badge_number": "CYBER-INV-5589",
            "phone_number": "+919876543211",
            "profile": {
                "organization": "National Cyber Forensics Lab",
                "department": "Anti-Money Laundering Cell",
                "experience_years": 5,
                "specialization": "Mixer De-anonymization & Bridge Tracking",
                "approval_status": InvestigatorApprovalStatus.APPROVED,
                "availability_status": InvestigatorAvailabilityStatus.AVAILABLE
            }
        },
        {
            "username": "inv_pending",
            "email": "amit.deshmukh@cybercrime.gov.in",
            "password": "password123",
            "role": UserRole.INVESTIGATOR,
            "full_name": "Cadet Amit Deshmukh",
            "badge_number": "CYBER-TRAINEE-01",
            "phone_number": "+919876543212",
            "profile": {
                "organization": "Regional Cyber Cell",
                "department": "Trainee Squad",
                "experience_years": 1,
                "specialization": "Digital Evidence Custody",
                "approval_status": InvestigatorApprovalStatus.PENDING,
                "availability_status": InvestigatorAvailabilityStatus.OFFLINE
            }
        },
        {
            "username": "supervisor",
            "email": "supervisor@cybercrime.gov.in",
            "password": "password123",
            "role": UserRole.SUPERVISOR,
            "full_name": "DSP Rajesh Kulkarni",
            "badge_number": "CYBER-DSP-1090",
            "phone_number": "+919876543220",
            "profile": None
        },
        {
            "username": "admin",
            "email": "admin@cybercrime.gov.in",
            "password": "password123",
            "role": UserRole.ADMINISTRATOR,
            "full_name": "System Administrator",
            "badge_number": "SYS-ADMIN-01",
            "phone_number": "+919876543200",
            "profile": None
        },
        {
            "username": "victim",
            "email": "rahul.sharma@example.com",
            "password": "password123",
            "role": UserRole.VICTIM,
            "full_name": "Rahul Sharma",
            "badge_number": None,
            "phone_number": "+919811223344",
            "profile": None
        },
        {
            "username": "victim2",
            "email": "ananya.sen@example.com",
            "password": "password123",
            "role": UserRole.VICTIM,
            "full_name": "Ananya Sen",
            "badge_number": None,
            "phone_number": "+919822334455",
            "profile": None
        }
    ]

    created = []
    for u in default_users:
        user = db.query(User).filter(User.username == u["username"]).first()
        if not user:
            user = User(
                username=u["username"],
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
                full_name=u["full_name"],
                badge_number=u["badge_number"],
                phone_number=u.get("phone_number")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created.append(u["username"])

        # Seed profile if investigator
        if u.get("profile"):
            prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == user.id).first()
            if not prof:
                prof_data = u["profile"]
                prof = InvestigatorProfile(
                    user_id=user.id,
                    organization=prof_data["organization"],
                    department=prof_data["department"],
                    experience_years=prof_data["experience_years"],
                    specialization=prof_data["specialization"],
                    badge_id=user.badge_number,
                    approval_status=prof_data["approval_status"],
                    availability_status=prof_data["availability_status"]
                )
                db.add(prof)
                db.commit()

    return {"message": "Multi-role accounts & investigator profiles ready", "created": created}

