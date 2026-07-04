from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class GenericSlot:
    slot_type: str
    label: str = ''
    icon: str = ''
    url: str = ''
    style: str = ''
    bento_size: str = 'standard'
    image: str = ''

    @property
    def average_rating(self) -> float:
        return 0.0

    @property
    def review_count(self) -> int:
        return 0

    @property
    def created_at(self):
        return None

    @property
    def is_filler(self) -> bool:
        return True
