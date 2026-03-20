from pydantic import BaseModel
from typing import Optional

class ConsultRequest(BaseModel):
    name: str
    cpf_nis: Optional[str] = None

class ConsultResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    details: Optional[list] = None
    error_msg: Optional[str] = None