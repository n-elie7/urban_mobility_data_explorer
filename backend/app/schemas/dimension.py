from pydantic import BaseModel


class VendorResponse(BaseModel):
    vendor_id: int
    name: str

    model_config = {"from_attributes": True}


class RateCodeResponse(BaseModel):
    rate_code_id: int
    description: str

    model_config = {"from_attributes": True}


class PaymentTypeResponse(BaseModel):
    payment_type_id: int
    description: str

    model_config = {"from_attributes": True}
