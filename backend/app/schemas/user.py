from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordReset(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class ForgotPassword(BaseModel):
    email: str


class ResendConfirmation(BaseModel):
    email: str


class ConfirmEmailResponse(BaseModel):
    message: str = "Email confirmed successfully"


class EmailConfirmed(BaseModel):
    message: str = "Email confirmed successfully"