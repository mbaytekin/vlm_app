from abc import ABC, abstractmethod
from typing import Dict, Any
from shared.schemas import ChatResponse

class IModelBackend(ABC):
    @abstractmethod
    def vision_chat(self, served_name:str, messages:list, gen_kwargs:Dict[str,Any]) -> ChatResponse: ...
    @abstractmethod
    def list_models(self) -> Any: ...
