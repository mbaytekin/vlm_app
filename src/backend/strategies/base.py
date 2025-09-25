from abc import ABC, abstractmethod
from typing import Dict, Any

class ITaskStrategy(ABC):
    @abstractmethod
    def build_messages(self, prompt:str, image_dataurl:str) -> list: ...

    @abstractmethod
    def parse_response(self, text:str) -> Any: ...
