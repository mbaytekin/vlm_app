/**
 * Application State Types
 * UI state yönetimi için type tanımları
 */

import { ModelInfo, TaskType } from "./api";

// Mesaj render bilgileri
export interface MessageRender {
  annotated_png_b64?: string;
  boxes?: Array<{
    label: string;
    x: number;
    y: number;
    w: number;
    h: number;
  }>;
}

// Chat mesajı
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  render?: MessageRender;
  timestamp: number;
}

// Thread (sohbet) state'i
export interface ThreadState {
  thread_id: string;
  history: ChatMessage[];
  preview_dataurl: string | null;
  created_at: number;
}

// Uygulama state'i
export interface AppState {
  // Model ve görev seçimi
  selectedModel: ModelInfo | null;
  selectedTask: TaskType;
  
  // Aktif thread
  currentThreadId: string | null;
  threads: Record<string, ThreadState>;
  
  // UI ayarları
  settings: {
    maxNewTokens: number;
    temperature: number;
    topP: number;
    presencePenalty: number;
    frequencyPenalty: number;
    freeMode: boolean;
    jsonStrict: boolean;
  };
  
  // Gateway durumu
  gatewayAlive: boolean;
  isLoading: boolean;
  error: string | null;
}

