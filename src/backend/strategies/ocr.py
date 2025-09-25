from .base import ITaskStrategy


class OCRStrategy(ITaskStrategy):
    def build_messages(self, prompt:str, image_dataurl:str)->list:
        sys = ("Yalnızca görseldeki yazıları sırayla çıkar. "
               "Sadece metin üret; ek açıklama verme.")

        p = prompt.strip() or "Görseldeki tüm metni sırayla yaz."
        
        return [{"role":"system","content":[{"type":"text","text":sys}]},
                {"role":"user","content":[{"type":"text","text":p},
                                          {"type":"input_image","image_url":image_dataurl}]}]
    def parse_response(self, text:str):
        return text.strip()