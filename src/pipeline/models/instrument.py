from pydantic import BaseModel, ConfigDict
from typing import Optional


class Instrument(BaseModel):
    """Represents a financial instrument record"""

    model_config = ConfigDict(frozen=True)

    Id: str
    FullNm: Optional[str] = None
    ClssfctnTp: Optional[str] = None
    CmmdtyDerivInd: Optional[str] = None
    NtnlCcy: Optional[str] = None
    Issr: Optional[str] = None
