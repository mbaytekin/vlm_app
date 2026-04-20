from .base import ITaskStrategy


class CaptionStrategy(ITaskStrategy):
    def build_messages(self, prompt: str, image_dataurl: str | None) -> list:
        p = prompt.strip() or ("Bu görseli ayrıntılı şekilde açıkla." if image_dataurl else "Bu konuyu ayrıntılı şekilde açıkla.")
        content = [{"type": "text", "text": p}]
        if image_dataurl:
            content.append({"type": "input_image", "image_url": image_dataurl})
        return [{"role": "user", "content": content}]

    def parse_response(self, text: str):
        return text.strip()
