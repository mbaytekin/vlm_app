from .base import ITaskStrategy

class DirectStrategy(ITaskStrategy):
    """Kullanıcının prompt'unu aynen iletir; hiçbir sistem/şablon eklemez."""
    def build_messages(self, prompt: str, image_dataurl: str | None) -> list:
        p = prompt.strip() or ("Görseli analiz et ve soruma yanıt ver." if image_dataurl else "Soruma yanıt ver.")
        content = [{"type": "text", "text": p}]
        if image_dataurl:
            content.append({"type": "input_image", "image_url": image_dataurl})
        return [{"role": "user", "content": content}]

    def parse_response(self, text: str):
        return text.strip()
