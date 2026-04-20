from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class ModelInfo(BaseModel):
    key: str
    title: str
    served_name: str
    notes: Optional[str] = None
    runtime: Literal["vllm", "direct"] = "vllm"
    supported_tasks: List[Literal["caption","vqa","ocr","detection"]] = ["caption","vqa"]

class ModelsResponse(BaseModel):
    models: List[ModelInfo]

class ModelStatusResponse(BaseModel):
    running: bool
    ready: bool
    pid: Optional[int] = None
    model_key: Optional[str] = None
    served_name: Optional[str] = None
    served_models: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    runtime: Optional[Literal["vllm", "direct"]] = None

class ThreadCreateResponse(BaseModel):
    thread_id: str
    preview_dataurl: Optional[str] = None

class ThreadItem(BaseModel):
    thread_id: str
    created_at: float

class ThreadsListResponse(BaseModel):
    items: List[ThreadItem]

class ChatTurnRequest(BaseModel):
    prompt: str
    task: Literal["caption","vqa","ocr","detection"] = "vqa"
    model_key: Optional[str] = None
    audio_dataurl: Optional[str] = None
    free_mode: bool = False
    json_strict: bool = True
    gen_kwargs: Dict[str, Any] = Field(default_factory=dict)

class ChatTurnResponse(BaseModel):
    text: str
    boxes: Optional[list] = None
    annotated_png_b64: Optional[str] = None
