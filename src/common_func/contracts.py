from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List

class GasPriceRecord(BaseModel):
    model_config = ConfigDict(extra='allow') # Keeps extra fields for additive drift detection
    timestamp: datetime
    commodity: str = Field(..., pattern=r"^[A-Z_]+$")
    price_close: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)

    @field_validator('price_close')
    @classmethod
    def price_sanity_check(cls, v: float) -> float:
        # Market-specific logic: TTF Gas rarely swings 500% in a day
        # This catches "Fat Finger" errors or API glitches
        if v > 1000: 
            raise ValueError(f"Extreme price detected: {v}. Potential drift or error.")
        return v

class GasPriceCollection(BaseModel):
    records: List[GasPriceRecord]