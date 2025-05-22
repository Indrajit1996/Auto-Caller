from pydantic import BaseModel


class UserRegisterResponse(BaseModel):
    message: str = "User registered successfully"
    status: str = "active"
