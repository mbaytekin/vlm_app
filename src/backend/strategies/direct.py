from .base import ITaskStrategy

class DirectStrategy(ITaskStrategy):
    """Kullanıcının prompt'unu aynen iletir; hiçbir sistem/şablon eklemez."""
    def build_messages(self, prompt: str, image_dataurl: str) -> list:
        p = prompt.strip() or "Görseli analiz et ve soruma yanıt ver."
        return [{
            "role": "user",
            "content": [
                {"type": "text", "text": p},
                {"type": "input_image", "image_url": image_dataurl}
            ]
        }]

    def parse_response(self, text: str):
        return text.strip()
