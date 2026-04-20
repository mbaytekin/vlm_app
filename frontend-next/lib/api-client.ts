/**
 * API Client
 * FastAPI gateway (http://localhost:9000) ile iletişim için HTTP client
 * Mevcut Python ApiClient ile uyumlu
 */

import {
  ModelsResponse,
  ModelInfo,
  ThreadCreateResponse,
  ThreadsListResponse,
  ChatTurnRequest,
  ChatTurnResponse,
  HealthResponse,
  ModelServeResponse,
  ModelStatusResponse,
} from "@/types/api";

const DEFAULT_API_URL = process.env.NEXT_PUBLIC_VLM_GATEWAY_URL || "http://localhost:9000";

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_API_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, ""); // Trailing slash'i kaldır
  }

  /**
   * Gateway'in çalışıp çalışmadığını kontrol eder
   */
  async checkHealth(): Promise<HealthResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
      }
      
      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("Gateway'e bağlanılamıyor (timeout)");
      }
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error(`Gateway'e bağlanılamıyor: ${this.baseUrl} - Backend çalışıyor mu?`);
      }
      throw error;
    }
  }

  /**
   * Mevcut modelleri listeler
   */
  async listModels(): Promise<ModelInfo[]> {
    const response = await fetch(`${this.baseUrl}/models`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Failed to list models: ${response.statusText}`);
    }

    const data: ModelsResponse = await response.json();
    return data.models;
  }

  /**
   * Belirtilen modeli başlatır (vLLM sunucusunda)
   */
  async serveModel(modelKey: string): Promise<ModelServeResponse> {
    const response = await fetch(`${this.baseUrl}/models/${modelKey}/serve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(error.error || `Failed to serve model: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Çalışan modeli durdurur
   */
  async stopModel(): Promise<ModelServeResponse> {
    const response = await fetch(`${this.baseUrl}/models/stop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Failed to stop model: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Çalışan model sürecinin durumunu döner
   */
  async getModelStatus(): Promise<ModelStatusResponse> {
    const response = await fetch(`${this.baseUrl}/models/status`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Failed to get model status: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Yeni bir thread (sohbet) oluşturur
   * @param file - Opsiyonel görsel dosyası
   */
  async createThread(file?: File, modelKey?: string): Promise<ThreadCreateResponse> {
    const formData = new FormData();
    if (file) {
      formData.append("file", file);
    }
    if (modelKey) {
      formData.append("model_key", modelKey);
    }

    // FormData gönderirken Content-Type header'ını EKLEME
    // Browser otomatik olarak multipart/form-data ekler
    const response = await fetch(`${this.baseUrl}/threads`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(error.error || `Failed to create thread: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Tüm thread'leri listeler
   */
  async listThreads(): Promise<ThreadsListResponse> {
    const response = await fetch(`${this.baseUrl}/threads`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Failed to list threads: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Belirtilen thread'i siler
   */
  async deleteThread(threadId: string): Promise<{ ok: boolean }> {
    const response = await fetch(`${this.baseUrl}/threads/${threadId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Failed to delete thread: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Thread'e yeni bir mesaj gönderir ve yanıt alır
   * @param threadId - Thread ID
   * @param payload - Chat isteği payload'ı
   */
  async chatTurn(threadId: string, payload: ChatTurnRequest): Promise<ChatTurnResponse> {
    // AbortController ile timeout ekle (120 saniye)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    try {
      const url = `${this.baseUrl}/threads/${threadId}/messages`;
      console.log("[API] Sending chat request to:", url);
      
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: response.statusText }));
        console.error("[API] Error response:", error);
        throw new Error(error.error || `Failed to send message: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("[API] Success response");
      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
        if (error.name === "AbortError") {
          throw new Error("İstek zaman aşımına uğradı (120 saniye). Lütfen tekrar deneyin.");
        }
        if (error.message.includes("NetworkError") || error.message.includes("Failed to fetch")) {
          throw new Error(`Backend'e bağlanılamıyor: ${this.baseUrl} - Gateway çalışıyor mu?`);
        }
        console.error("[API] Chat error:", error);
        throw error;
      }
      throw new Error("Bilinmeyen bir hata oluştu");
    }
  }
}

// Singleton instance
export const apiClient = new ApiClient();
