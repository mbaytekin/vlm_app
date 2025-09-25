from .base import ITaskStrategy


class CaptionStrategy(ITaskStrategy):
    def build_messages(self, prompt:str, image_dataurl:str)->list:
        p = prompt.strip() or "Bu görseli ayrıntılı şekilde açıkla."
        return [{"role":"user","content":[{"type":"text","text":p},
                                         {"type":"input_image","image_url":image_dataurl}]}]
    def parse_response(self, text:str):
        return text.strip()