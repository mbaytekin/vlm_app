from abc import ABC, abstractmethod
from typing import Any

class ITaskStrategy(ABC):
    @abstractmethod
    def build_messages(self, prompt: str, image_dataurl: str | None) -> list: ...

    @abstractmethod
    def parse_response(self, text:str) -> Any: ...
