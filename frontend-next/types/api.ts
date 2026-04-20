/**
 * API Type Definitions
 * FastAPI gateway ile uyumlu type tanımları
 */

// Model bilgileri
export interface ModelInfo {
  key: string;
  title: string;
  served_name: string;
  notes?: string;
  runtime?: "vllm" | "direct";
  supported_tasks?: Array<"caption" | "vqa" | "ocr" | "detection">;
}

export interface ModelsResponse {
  models: ModelInfo[];
}

export interface ModelStatusResponse {
  running: boolean;
  ready: boolean;
  pid?: number | null;
  model_key?: string | null;
  served_name?: string | null;
  served_models: string[];
  error?: string | null;
  runtime?: "vllm" | "direct" | null;
}

// Thread (sohbet) yönetimi
export interface ThreadCreateResponse {
  thread_id: string;
  preview_dataurl: string | null;
}

export interface ThreadItem {
  thread_id: string;
  created_at: number;
}

export interface ThreadsListResponse {
  items: ThreadItem[];
}

// Chat mesajları
export type TaskType = "caption" | "vqa" | "ocr" | "detection";

export interface ChatTurnRequest {
  prompt: string;
  task?: TaskType;
  model_key?: string;
  audio_dataurl?: string;
  free_mode?: boolean;
  json_strict?: boolean;
  gen_kwargs?: {
    max_tokens?: number;
    temperature?: number;
    top_p?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
  };
}

export interface ChatTurnResponse {
  text: string;
  boxes?: Array<{
    label: string;
    x: number;
    y: number;
    w: number;
    h: number;
  }>;
  annotated_png_b64?: string;
}

// Health check
export interface HealthResponse {
  ok: boolean;
}

// Model kontrol
export interface ModelServeResponse {
  ok: boolean;
  pid?: number;
}
