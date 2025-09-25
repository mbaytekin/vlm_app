from pydantic import BaseModel, Field
from typing import List, Optional, Literal

TaskType = Literal["caption","vqa","ocr","detection"]

class ModelInfo(BaseModel):
    key: str
    title: str
    hf_id: str
    served_name: str
    notes: Optional[str] = None
    quant: Optional[str] = None
    supported_tasks: List[Literal["caption","vqa","ocr","detection"]] = ["caption","vqa"]

class VisionRequest(BaseModel):
    model_key: str
    task: TaskType
    prompt: str
    image_b64: str
    max_new_tokens: int = 256
    temperature: float = 0.2
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

class DetectionBox(BaseModel):
    label: str
    x: int
    y: int
    w: int
    h: int

class DetectionResult(BaseModel):
    boxes: List[DetectionBox]

class ChatResponse(BaseModel):
    text: str
