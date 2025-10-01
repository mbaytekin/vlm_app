# VLM App

# Görsel ve metin girdileriyle çalışan çok modlu (multimodal) modelleri test etmek için geliştirilmiş bir demo arayüzdür.
# Uygulama, Streamlit tabanlı bir kullanıcı arayüzü sunar ve arka planda vLLM tabanlı bir backend servisiyle haberleşir.

# --------------------------------------------------------------------------------
# Gereksinimler
# - Python 3.10 veya üzeri
# - NVIDIA GPU (CUDA 12.1)
# - Conda (önerilir)
# --------------------------------------------------------------------------------

# Kurulum
conda env create -f environment.yml
conda activate vlm-ui

# --------------------------------------------------------------------------------
# Model Hazırlığı (isteğe bağlı)
# Yerel ortama modelleri indirmek için aşağıdaki komutu çalıştırın.
python scripts/prepare_models.py --keys qwen2_5_vl_7b_awq

# Hugging Face token'ınız varsa `.env` dosyasına ekleyebilirsiniz.
# --------------------------------------------------------------------------------

# vLLM Sunucusunu Başlatma
# Backend servis katmanını başlatmak için:
python scripts/serve_vllm.py --model-key qwen2_5_vl_7b_awq

# Bu komut `configs/models.yaml` dosyasındaki ilgili modeli yükler
# ve `http://localhost:8000/v1` adresinde REST API'yi açar.

# Sunucu durumunu kontrol etmek için:
python scripts/healthcheck.py

# --------------------------------------------------------------------------------
# Kullanıcı Arayüzünü Başlatma
# Ayrı bir terminalde aşağıdaki komutu çalıştırın.
streamlit run src/ui/app.py

# Tarayıcıda otomatik olarak açılır:
# http://localhost:8501
# --------------------------------------------------------------------------------

# Kullanım
# 1. Arayüzde model ve görev seçimi yapın
# 2. Görsel yükleyin
# 3. Üretim parametrelerini ayarlayın (max_new_tokens, temperature, vb.)
# 4. Çalıştır butonuna basın
# 5. Sonucu görüntüleyin:
#    - caption, vqa, ocr: metin cevabı
#    - detection: kutular çizilmiş görsel ve JSON formatında çıktı

# --------------------------------------------------------------------------------
# Bilinmesi Gerekenler
# - GPU belleği yetersizse `configs/models.yaml` içindeki `gpu_memory_utilization` değerini düşürebilirsiniz.
# - Görsel uzun kenarı, `configs/app.yaml` dosyasındaki `limits.max_image_long_side` değeri ile sınırlandırılır.
# - `trust_remote_code: true` ayarı yalnızca güvenilir modeller için kullanılmalıdır.