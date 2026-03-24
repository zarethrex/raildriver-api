import pydantic


class LocoInfo(pydantic.BaseModel):
    author: str
    product: str
    train: str
