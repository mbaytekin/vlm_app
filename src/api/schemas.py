from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class ModelInfo(BaseModel):
    key: str
    title: str
    served_name: str
    notes: Optional[str] = None
    supported_tasks: List[Literal["caption","vqa","ocr","detection"]] = ["caption","vqa"]

class ModelsResponse(BaseModel):
    models: List[ModelInfo]

class ThreadCreateResponse(BaseModel):
    thread_id: str
    preview_dataurl: str

class ThreadItem(BaseModel):
    thread_id: str
    created_at: float

class ThreadsListResponse(BaseModel):
    items: List[ThreadItem]

class ChatTurnRequest(BaseModel):
    prompt: str
    task: Literal["caption","vqa","ocr","detection"] = "vqa"
    free_mode: bool = False
    json_strict: bool = True
    gen_kwargs: Dict[str, Any] = Field(default_factory=dict)

class ChatTurnResponse(BaseModel):
    text: str
    boxes: Optional[list] = None
    annotated_png_b64: Optional[str] = None
