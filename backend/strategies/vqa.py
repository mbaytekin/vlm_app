from .base import ITaskStrategy


class VQAStrategy(ITaskStrategy):
    def build_messages(self, prompt: str, image_dataurl: str | None) -> list:
        p = prompt.strip() or ("Görsele bakarak sorumu cevapla." if image_dataurl else "Sorumu cevapla.")
        content = [{"type": "text", "text": p}]
        if image_dataurl:
            content.append({"type": "input_image", "image_url": image_dataurl})
        return [{"role": "user", "content": content}]

    def parse_response(self, text: str):
        return text.strip()
