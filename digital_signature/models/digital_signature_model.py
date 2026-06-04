from pydantic.main import BaseModel
from typing import Optional


class SignDigitally(BaseModel):
    epr_plastic: Optional[str]
    company_id: Optional[int]
    application_id: Optional[int]
    request_id : Optional[int]
