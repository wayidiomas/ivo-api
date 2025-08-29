from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import re

class UserBase(BaseModel):
    email: str
    phone: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Email inválido')
        return v

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AuthRequest(BaseModel):
    email: str = Field(..., description="Email do usuário")
    api_key_ivo: str = Field(..., description="Chave de acesso IVO")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Email inválido')
        return v

class AuthResponse(BaseModel):
    access_token: str = Field(..., description="Token Bearer para acesso à API V2")
    token_type: str = Field(default="bearer")
    user_id: Optional[str] = None
    scopes: List[str] = Field(default_factory=lambda: ["v2_access"])
    expires_at: Optional[datetime] = None
    rate_limit: Dict[str, int] = Field(default_factory=lambda: {
        "requests_per_minute": 100,
        "requests_per_hour": 1000
    })

class TokenInfo(BaseModel):
    id: uuid.UUID
    token_ivo: str
    token_bearer: str
    user_id: Optional[str] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=lambda: ["v2_access"])
    rate_limit_config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int = 0

    class Config:
        from_attributes = True

class CreateUserRequest(BaseModel):
    email: str
    phone: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    scopes: List[str] = Field(default_factory=lambda: ["v2_access"])
    rate_limit_config: Dict[str, int] = Field(default_factory=lambda: {
        "requests_per_minute": 100,
        "requests_per_hour": 1000
    })
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Email inválido')
        return v

class CreateUserResponse(BaseModel):
    user: UserResponse
    token_info: AuthResponse
    message: str = "Usuário e token criados com sucesso"