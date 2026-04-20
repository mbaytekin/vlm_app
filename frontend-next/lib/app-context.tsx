/**
 * App Context
 * Uygulama genelinde state yönetimi için React Context
 */

"use client";

import React, { createContext, useContext, useReducer, useEffect, useCallback } from "react";
import { AppState, ChatMessage } from "@/types/state";
import { ModelInfo, TaskType, ChatTurnRequest } from "@/types/api";
import { apiClient } from "./api-client";

// Initial state
const initialState: AppState = {
  selectedModel: null,
  selectedTask: "caption",
  currentThreadId: null,
  threads: {},
  settings: {
    maxNewTokens: 256,
    temperature: 0.2,
    topP: 1.0,
    presencePenalty: 0.0,
    frequencyPenalty: 0.0,
    freeMode: false,
    jsonStrict: true,
  },
  gatewayAlive: false,
  isLoading: false,
  error: null,
};

// Action types
type AppAction =
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "SET_GATEWAY_ALIVE"; payload: boolean }
  | { type: "SET_SELECTED_MODEL"; payload: ModelInfo | null }
  | { type: "SET_SELECTED_TASK"; payload: TaskType }
  | { type: "UPDATE_SETTINGS"; payload: Partial<AppState["settings"]> }
  | { type: "CREATE_THREAD"; payload: { threadId: string; previewDataurl: string | null } }
  | { type: "SET_CURRENT_THREAD"; payload: string | null }
  | { type: "ADD_MESSAGE"; payload: { threadId: string; message: ChatMessage } }
  | { type: "CLEAR_THREAD_HISTORY"; payload: string }
  | { type: "CLEAR_ALL_THREADS" };

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    
    case "SET_ERROR":
      return { ...state, error: action.payload };
    
    case "SET_GATEWAY_ALIVE":
      return { ...state, gatewayAlive: action.payload };
    
    case "SET_SELECTED_MODEL":
      return { ...state, selectedModel: action.payload };
    
    case "SET_SELECTED_TASK":
      return { ...state, selectedTask: action.payload };
    
    case "UPDATE_SETTINGS":
      return { ...state, settings: { ...state.settings, ...action.payload } };
    
    case "CREATE_THREAD":
      return {
        ...state,
        threads: {
          ...state.threads,
          [action.payload.threadId]: {
            thread_id: action.payload.threadId,
            history: [],
            preview_dataurl: action.payload.previewDataurl,
            created_at: Date.now(),
          },
        },
        currentThreadId: action.payload.threadId,
      };
    
    case "SET_CURRENT_THREAD":
      return { ...state, currentThreadId: action.payload };
    
    case "ADD_MESSAGE": {
      const { threadId, message } = action.payload;
      const thread = state.threads[threadId];
      if (!thread) return state;
      
      return {
        ...state,
        threads: {
          ...state.threads,
          [threadId]: {
            ...thread,
            history: [...thread.history, message],
          },
        },
      };
    }
    
    case "CLEAR_THREAD_HISTORY": {
      const thread = state.threads[action.payload];
      if (!thread) return state;
      
      return {
        ...state,
        threads: {
          ...state.threads,
          [action.payload]: {
            ...thread,
            history: [],
          },
        },
      };
    }
    
    case "CLEAR_ALL_THREADS":
      return {
        ...state,
        threads: {},
        currentThreadId: null,
      };
    
    default:
      return state;
  }
}

// Context
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  // Helper functions
  createThread: (file?: File) => Promise<void>;
  sendMessage: (prompt: string, audioFile?: File) => Promise<void>;
  clearThreadHistory: () => void;
  clearAllThreads: () => void;
  checkGatewayHealth: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider component
export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const fileToDataUrl = useCallback((file: File) => {
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(new Error("Ses dosyası okunamadı."));
      reader.readAsDataURL(file);
    });
  }, []);

  // Gateway health check
  const checkGatewayHealth = useCallback(async () => {
    try {
      await apiClient.checkHealth();
      dispatch({ type: "SET_GATEWAY_ALIVE", payload: true });
      dispatch({ type: "SET_ERROR", payload: null });
    } catch (error) {
      dispatch({ type: "SET_GATEWAY_ALIVE", payload: false });
      dispatch({ type: "SET_ERROR", payload: "Gateway bağlantısı yok" });
    }
  }, []);

  // Periodic health check
  useEffect(() => {
    checkGatewayHealth();
    const interval = setInterval(checkGatewayHealth, 10000); // Her 10 saniyede bir
    return () => clearInterval(interval);
  }, [checkGatewayHealth]);

  // Create thread
  const createThread = useCallback(async (file?: File) => {
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });
    
    try {
      const response = await apiClient.createThread(file, state.selectedModel?.key);
      dispatch({
        type: "CREATE_THREAD",
        payload: {
          threadId: response.thread_id,
          previewDataurl: response.preview_dataurl,
        },
      });
    } catch (error) {
      dispatch({ type: "SET_ERROR", payload: (error as Error).message });
      throw error;
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  }, [state.selectedModel]);

  // Send message
  const sendMessage = useCallback(async (prompt: string, audioFile?: File) => {
    if (!state.currentThreadId) return;
    
    const thread = state.threads[state.currentThreadId];
    if (!thread) return;

    // Kullanıcı mesajını ekle
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}-${Math.random()}`,
      role: "user",
      text: prompt,
      timestamp: Date.now(),
    };
    
    dispatch({
      type: "ADD_MESSAGE",
      payload: { threadId: state.currentThreadId, message: userMessage },
    });

    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });

    try {
      let audioDataurl: string | undefined;
      if (audioFile) {
        audioDataurl = await fileToDataUrl(audioFile);
      }

      const payload: ChatTurnRequest = {
        prompt,
        task: state.selectedTask,
        model_key: state.selectedModel?.key,
        audio_dataurl: audioDataurl,
        free_mode: state.settings.freeMode,
        json_strict: state.settings.jsonStrict,
        gen_kwargs: {
          max_tokens: state.settings.maxNewTokens,
          temperature: state.settings.temperature,
          top_p: state.settings.topP,
          presence_penalty: state.settings.presencePenalty,
          frequency_penalty: state.settings.frequencyPenalty,
        },
      };

      const response = await apiClient.chatTurn(state.currentThreadId, payload);

      // Assistant mesajını ekle
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}-${Math.random()}`,
        role: "assistant",
        text: response.text || " ",
        render: response.boxes || response.annotated_png_b64
          ? {
              boxes: response.boxes,
              annotated_png_b64: response.annotated_png_b64,
            }
          : undefined,
        timestamp: Date.now(),
      };

      dispatch({
        type: "ADD_MESSAGE",
        payload: { threadId: state.currentThreadId, message: assistantMessage },
      });
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}-${Math.random()}`,
        role: "assistant",
        text: `Hata: ${(error as Error).message}`,
        timestamp: Date.now(),
      };
      
      dispatch({
        type: "ADD_MESSAGE",
        payload: { threadId: state.currentThreadId, message: errorMessage },
      });
      
      dispatch({ type: "SET_ERROR", payload: (error as Error).message });
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  }, [fileToDataUrl, state.currentThreadId, state.threads, state.selectedModel, state.selectedTask, state.settings]);

  // Clear thread history
  const clearThreadHistory = useCallback(() => {
    if (state.currentThreadId) {
      dispatch({ type: "CLEAR_THREAD_HISTORY", payload: state.currentThreadId });
    }
  }, [state.currentThreadId]);

  // Clear all threads
  const clearAllThreads = useCallback(() => {
    dispatch({ type: "CLEAR_ALL_THREADS" });
  }, []);

  const value: AppContextType = {
    state,
    dispatch,
    createThread,
    sendMessage,
    clearThreadHistory,
    clearAllThreads,
    checkGatewayHealth,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

// Hook
export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}
