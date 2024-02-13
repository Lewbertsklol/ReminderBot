from dataclasses import dataclass
from typing import Any


@dataclass
class Item:
    name: str | None = None
    maker: str | None = None
    size: str | None = None
    price: str | None = None

    def __eq__(self, __value: object) -> bool:
        return self.name == __value.name and self.maker == __value.maker

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "maker": self.maker,
            "price": self.price,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Item":
        return cls(**data)
