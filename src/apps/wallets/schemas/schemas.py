from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, AliasGenerator
from pydantic.alias_generators import to_camel


class WalletSchema(BaseModel):
    balance: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, alias_generator=AliasGenerator(serialization_alias=to_camel))



class WalletResponseSchema(BaseModel):
    uuid: UUID
    balance: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, alias_generator=AliasGenerator(serialization_alias=to_camel))



class WalletDataOperationsSchema(BaseModel):
    uuid: UUID
    amount: Decimal = Field(default=Decimal("0.00"), ge=0)

    model_config = ConfigDict(from_attributes=True,
                              alias_generator=AliasGenerator(serialization_alias=to_camel))



class WalletCreate(BaseModel):
    balance: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)

    model_config = ConfigDict(from_attributes=True, alias_generator=AliasGenerator(serialization_alias=to_camel))


class WalletUpdateSchema(BaseModel):
    balance: Decimal = Field(ge=0)

    model_config = ConfigDict(from_attributes=True, alias_generator=AliasGenerator(serialization_alias=to_camel))
