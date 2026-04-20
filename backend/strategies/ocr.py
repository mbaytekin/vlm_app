from .base import ITaskStrategy


class OCRStrategy(ITaskStrategy):
    def build_messages(self, prompt: str, image_dataurl: str | None) -> list:
        sys = ("Yalnızca görseldeki yazıları sırayla çıkar. "
               "Sadece metin üret; ek açıklama verme.")

        p = prompt.strip() or ("Görseldeki tüm metni sırayla yaz." if image_dataurl else "Metni sırayla yaz.")
        user_content = [{"type": "text", "text": p}]
        if image_dataurl:
            user_content.append({"type": "input_image", "image_url": image_dataurl})
        return [{"role": "system", "content": [{"type": "text", "text": sys}]},
                {"role": "user", "content": user_content}]

    def parse_response(self, text: str):
        return text.strip()
