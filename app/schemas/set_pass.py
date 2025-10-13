from pydantic import BaseModel, Field

class SetPasswordRequest(BaseModel):
    p: str = Field(..., min_length=8, description="New password, min 8 chars")
