# VLM App

VLM App is a local multimodal model gateway with a modern web interface for testing vision-language models across captioning, visual question answering, OCR, and detection workflows. The backend exposes a FastAPI gateway and can route requests either to a managed vLLM server or to an in-process Transformers runtime for models that are better served directly.

## Highlights

- FastAPI gateway for model discovery, runtime control, health checks, and thread-based chat.
- Next.js 14 and TypeScript frontend with model selection, task selection, image upload, chat history, and runtime status.
- Runtime switching between vLLM-backed models and direct Transformers models.
- Default direct 4-bit Gemma runtime for lower VRAM setups.
- Optional vLLM process management from the UI or CLI.
- Text-only threads as well as image-backed multimodal threads.
- Structured detection responses with optional annotated image output.

## Architecture

```text
frontend-next/          Next.js web client
backend/api/            FastAPI gateway, routers, request schemas, runtime services
backend/registry/       Model registry and vLLM process launcher
backend/strategies/     Prompt and response strategies for caption, VQA, OCR, detection, direct chat
backend/providers/      Provider clients for vLLM-compatible APIs
shared/                 Shared configuration, schemas, logging, and errors
configs/                Application and model configuration
scripts/                Model preparation, vLLM launcher, and health checks
frontend-streamlit-old/ Legacy Streamlit frontend retained for reference
```

The browser talks to the gateway on `http://localhost:9000`. vLLM models are served through an OpenAI-compatible server on `http://localhost:8000/v1`. Direct models are loaded inside the gateway process and do not require a separate vLLM server.

## Requirements

- Python 3.10
- Node.js 18 or newer
- Conda or Mamba
- NVIDIA GPU with CUDA support for vLLM and accelerated direct runtime usage
- Hugging Face access where required by the selected model

## Setup

Create and activate the Python environment:

```bash
conda env create -f environment.yml
conda activate vlm-ui
```

Install or update the model runtime packages when working with the latest Gemma and vLLM support:

```bash
python -m pip install --upgrade --pre vllm
python -m pip install --upgrade git+https://github.com/huggingface/transformers.git
python -m pip install --upgrade accelerate "bitsandbytes>=0.48.1"
```

Install the frontend dependencies:

```bash
cd frontend-next
npm install
```

Optional environment variables:

```bash
HF_TOKEN=your_huggingface_token
OPENAI_API_BASE=http://localhost:8000/v1
NEXT_PUBLIC_VLM_GATEWAY_URL=http://localhost:9000
```

## Running Locally

Start the gateway:

```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 9000 --reload
```

Start the Next.js frontend in a separate terminal:

```bash
cd frontend-next
npm run dev
```

Open the UI at `http://localhost:3000`.

For direct-runtime models such as `gemma4_e4b_it_8bit`, no vLLM process is required. The gateway loads the model on demand when it is selected or when the first request is sent.

For vLLM-backed models, start the model manually:

```bash
python scripts/serve_vllm.py --model-key qwen2_5_vl_7b_awq --restart
```

Or use the frontend runtime controls to start and stop models through the gateway.

## Health Checks

```bash
python scripts/healthcheck_gateway.py
python scripts/healthcheck_vllm.py
```

The gateway also exposes:

- `GET /health`
- `GET /models`
- `GET /models/status`
- `POST /models/{key}/serve`
- `POST /models/stop`
- `POST /threads`
- `GET /threads`
- `DELETE /threads/{thread_id}`
- `POST /threads/{thread_id}/messages`

## Model Configuration

Models are configured in `configs/models.yaml`. The current default model is:

```yaml
default_model_key: gemma4_e4b_it_8bit
```

Supported model entries include:

| Key | Runtime | Notes |
| --- | --- | --- |
| `gemma4_e4b_it_8bit` | direct | Gemma 4 E4B via Transformers and BitsAndBytes 4-bit quantization. Recommended default for 16 GB VRAM class machines. |
| `gemma4_e4b_it` | vLLM | Gemma 4 E4B through vLLM with image and audio prompt limits configured. |
| `gemma4_e4b_unsloth_gguf` | vLLM/GGUF config | Included for experimentation, but Gemma 4 GGUF is currently treated as unstable by the launcher. |
| `qwen2_5_vl_7b_awq` | vLLM | Qwen2.5-VL 7B AWQ for captioning, VQA, OCR, and detection. |
| `phi_3_5_vision` | vLLM | Phi-3.5 Vision Instruct for captioning, VQA, and OCR. |
| `llava_1_5_7b` | vLLM | LLaVA 1.5 7B for captioning and VQA. |
| `internvl2_8b` | vLLM | InternVL2-8B for captioning and VQA. |

To prepare local model files where applicable:

```bash
python scripts/prepare_models.py
```

The preparation script respects per-model `download_allow_patterns`, which is useful for GGUF models that should only download selected files.

## Runtime Behavior

- Selecting a direct model stops any managed vLLM process and loads the model inside the gateway.
- Selecting a vLLM model unloads the direct runtime, stops any existing managed vLLM process, and starts the selected vLLM server.
- The launcher records `vllm.pid` and `vllm.model`, cleans stale port `8000` processes when restarting, and reports readiness from the OpenAI-compatible `/models` endpoint.
- Image uploads are resized according to `configs/app.yaml` to reduce VRAM pressure.
- OCR and detection require an image-backed thread. Text-only threads are supported for general chat, captioning-style prompts, and VQA-style prompts where the selected model can respond without an image.

## Frontend

The active frontend lives in `frontend-next/` and uses:

- Next.js App Router
- React 18
- TypeScript
- React Context for app state
- CSS variables for theme support

The previous Streamlit frontend was moved to `frontend-streamlit-old/` and is kept only as a reference implementation.

## Development Notes

- Keep model definitions in `configs/models.yaml`; the gateway and launcher both read from the same registry.
- Use `NEXT_PUBLIC_VLM_GATEWAY_URL` when the frontend must point to a non-default gateway host.
- Use `OPENAI_API_BASE` when the gateway should talk to a non-default vLLM endpoint.
- Gemma 4 GGUF is intentionally blocked by the launcher because that path is not stable with the current vLLM setup. Prefer `gemma4_e4b_it_8bit` for direct runtime or `gemma4_e4b_it` for vLLM.
