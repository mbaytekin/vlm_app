# Hızlı Başlangıç

## 0) Conda ortamı

```bash
conda env create -f environment.yml
conda activate vlm_app
```

## 1) Ortam paketleri (Terminal 1)

```bash
/home/db21052/anaconda3/envs/vlm_app/bin/python -m pip install --upgrade --pre vllm
/home/db21052/anaconda3/envs/vlm_app/bin/python -m pip install --upgrade git+https://github.com/huggingface/transformers.git
/home/db21052/anaconda3/envs/vlm_app/bin/python -m pip install --upgrade accelerate "bitsandbytes>=0.48.1"
```

## 2) Backend Gateway (Terminal 2)

```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 9000 --reload
```

Gateway portu: `http://localhost:9000`

## 3) Frontend Next.js (Terminal 3)

```bash
cd frontend-next
npm install
npm run dev
```

UI: `http://localhost:3000`

## 4) vLLM (sadece vLLM modeli sececeksen)

Varsayılan Gemma modeli direct runtime ile çalıştığı için bu adım zorunlu değil. Qwen/Phi/LLaVA gibi vLLM modellerini elle açmak istersen:

```bash
python scripts/serve_vllm.py --model-key qwen2_5_vl_7b_awq --restart
```

vLLM portu: `http://localhost:8000`

## 5) Sağlık kontrolü

```bash
python scripts/healthcheck_vllm.py
python scripts/healthcheck_gateway.py
```

## Notlar

- Sıra: `Gateway -> Frontend` (Gemma direct). vLLM modeli kullanacaksan `vLLM -> Gateway -> Frontend`.
- Model değişimi UI'den otomatik tetiklenir; runtime kartında `Yükleniyor/Hazır` görülebilir.
- `gemma4_e4b_it_8bit` artık direct runtime (Transformers+4bit). Bu model seçilince varsa vLLM süreci durdurulur.
- Gemma 4 için text-only sohbet açabilirsiniz (resim zorunlu değil).
- `gemma4_e4b_unsloth_gguf` (GGUF) seçeneği vLLM tarafında stabil değildir; mümkünse `gemma4_e4b_it_8bit` (direct) kullanın.
