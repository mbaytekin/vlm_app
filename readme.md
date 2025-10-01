# 🧠 VLM App

**VLM App**, görsel ve metin girdileriyle çalışan çok modlu (multimodal) modelleri test etmek için geliştirilmiş bir demo arayüzüdür.  
Uygulama, **Streamlit** tabanlı bir kullanıcı arayüzü sunar ve arka planda **vLLM** tabanlı bir backend servisiyle haberleşir.

---

## 🚀 Gereksinimler

- 🐍 **Python 3.10+**  
- 💻 **NVIDIA GPU (CUDA 12.1)**  
- 📦 **Conda** *(önerilir)*

---

## ⚙️ Kurulum

### 1. Ortamı oluşturun ve etkinleştirin:
```bash
conda env create -f environment.yml
conda activate vlm-ui

📦 Model Hazırlığı (isteğe bağlı)

Yerel ortama modelleri indirmek için:

python scripts/prepare_models.py --keys qwen2_5_vl_7b_awq

    💡 Not: Hugging Face token’ınız varsa .env dosyasına ekleyebilirsiniz.

🧠 vLLM Sunucusunu Başlatma

Backend servis katmanını başlatmak için:

python scripts/serve_vllm.py --model-key qwen2_5_vl_7b_awq

Bu komut:

    configs/models.yaml dosyasındaki ilgili modeli yükler

    REST API’yi http://localhost:8000/v1 adresinde açar

Sunucu durumunu kontrol etmek için:

python scripts/healthcheck.py

💻 Kullanıcı Arayüzünü Başlatma

Ayrı bir terminalde:

streamlit run src/ui/app.py

Tarayıcıda otomatik olarak açılır:
👉 http://localhost:8501
