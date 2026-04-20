/**
 * Sidebar Component
 * Model, task and runtime controls
 */

"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Play, RefreshCw, RotateCcw, Settings, Sparkles, Square, Trash2 } from "lucide-react";

import { useApp } from "@/lib/app-context";
import { apiClient } from "@/lib/api-client";
import { ModelInfo, ModelStatusResponse, TaskType } from "@/types/api";
import { cn } from "@/lib/utils";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

interface SidebarProps {
  className?: string;
}

type Notice = { type: "success" | "error"; text: string } | null;

export function Sidebar({ className }: SidebarProps) {
  const { state, dispatch } = useApp();
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [modelError, setModelError] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatusResponse | null>(null);
  const [switchingModelKey, setSwitchingModelKey] = useState<string | null>(null);
  const [isRefreshingStatus, setIsRefreshingStatus] = useState(false);
  const autoSwitchLockRef = useRef<string | null>(null);

  const pushNotice = useCallback((type: "success" | "error", text: string) => {
    setNotice({ type, text });
  }, []);

  const refreshModelStatus = useCallback(
    async (options?: { quiet?: boolean }) => {
      const quiet = options?.quiet ?? false;
      if (!quiet) {
        setIsRefreshingStatus(true);
      }
      try {
        const status = await apiClient.getModelStatus();
        setModelStatus(status);
        return status;
      } catch (error) {
        const msg = (error as Error).message;
        if (!quiet) {
          dispatch({ type: "SET_ERROR", payload: msg });
        }
        return null;
      } finally {
        if (!quiet) {
          setIsRefreshingStatus(false);
        }
      }
    },
    [dispatch]
  );

  const waitForModelReady = useCallback(
    async (modelKey: string, timeoutMs: number = 180000) => {
      const startedAt = Date.now();
      while (Date.now() - startedAt < timeoutMs) {
        const status = await refreshModelStatus({ quiet: true });
        if (status && status.model_key === modelKey && status.ready) {
          return true;
        }
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
      }
      return false;
    },
    [refreshModelStatus]
  );

  const serveModelAndWait = useCallback(
    async (modelKey: string, showNotice: boolean = true) => {
      const runtime = models.find((m) => m.key === modelKey)?.runtime ?? "vllm";
      setSwitchingModelKey(modelKey);
      dispatch({ type: "SET_ERROR", payload: null });
      try {
        await apiClient.serveModel(modelKey);
        setModelStatus((prev) =>
          prev
            ? { ...prev, running: true, ready: false, model_key: modelKey, runtime }
            : {
                running: true,
                ready: false,
                model_key: modelKey,
                pid: null,
                served_models: [],
                runtime,
              }
        );
        if (showNotice) {
          pushNotice("success", "Model yükleniyor...");
        }

        const ready = await waitForModelReady(modelKey);
        if (!ready) {
          throw new Error("Model belirtilen sürede hazır olmadı.");
        }
        if (showNotice) {
          const modelTitle = models.find((m) => m.key === modelKey)?.title || modelKey;
          pushNotice("success", `${modelTitle} hazır.`);
        }
      } catch (error) {
        const msg = (error as Error).message;
        dispatch({ type: "SET_ERROR", payload: msg });
        pushNotice("error", msg);
      } finally {
        setSwitchingModelKey(null);
      }
    },
    [dispatch, models, pushNotice, waitForModelReady]
  );

  useEffect(() => {
    if (models.length > 0) return;

    let active = true;
    async function loadModels() {
      try {
        const modelList = await apiClient.listModels();
        if (!active) return;

        setModels(modelList);
        if (modelList.length > 0) {
          const keep = state.selectedModel
            ? modelList.find((m) => m.key === state.selectedModel?.key) || modelList[0]
            : modelList[0];
          dispatch({ type: "SET_SELECTED_MODEL", payload: keep });
        }
      } catch (error) {
        if (!active) return;
        setModelError((error as Error).message);
      } finally {
        if (active) {
          setLoadingModels(false);
          await refreshModelStatus({ quiet: true });
        }
      }
    }

    loadModels();
    return () => {
      active = false;
    };
  }, [dispatch, models.length, refreshModelStatus, state.selectedModel]);

  useEffect(() => {
    if (!state.gatewayAlive) {
      setModelStatus(null);
      autoSwitchLockRef.current = null;
      return;
    }
    void refreshModelStatus({ quiet: true });
    const interval = window.setInterval(() => {
      void refreshModelStatus({ quiet: true });
    }, 2500);
    return () => window.clearInterval(interval);
  }, [refreshModelStatus, state.gatewayAlive]);

  useEffect(() => {
    if (!notice) return;
    const timeout = window.setTimeout(() => setNotice(null), 3000);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  const allTasks: TaskType[] = ["caption", "vqa", "ocr", "detection"];
  const availableTasks = useMemo(() => {
    const allowedTasks = state.selectedModel?.supported_tasks;
    if (!allowedTasks || allowedTasks.length === 0) {
      return allTasks;
    }
    return allTasks.filter((task) => allowedTasks.includes(task));
  }, [state.selectedModel]);

  useEffect(() => {
    if (availableTasks.length === 0) return;
    if (!availableTasks.includes(state.selectedTask)) {
      dispatch({ type: "SET_SELECTED_TASK", payload: availableTasks[0] });
    }
  }, [availableTasks, dispatch, state.selectedTask]);

  const handleModelChange = (value: string) => {
    const selected = models.find((model) => model.key === value);
    if (selected) {
      autoSwitchLockRef.current = null;
      dispatch({ type: "SET_SELECTED_MODEL", payload: selected });
    }
  };

  const handleTaskChange = (value: string) => {
    dispatch({ type: "SET_SELECTED_TASK", payload: value as TaskType });
  };

  const handleServeModel = async () => {
    if (!state.selectedModel) return;
    autoSwitchLockRef.current = state.selectedModel.key;
    await serveModelAndWait(state.selectedModel.key);
  };

  const handleStopModel = async () => {
    try {
      await apiClient.stopModel();
      dispatch({ type: "SET_ERROR", payload: null });
      autoSwitchLockRef.current = state.selectedModel?.key || null;
      await refreshModelStatus({ quiet: true });
      pushNotice("success", "Model süreci durduruldu.");
    } catch (error) {
      const msg = (error as Error).message;
      dispatch({ type: "SET_ERROR", payload: msg });
      pushNotice("error", msg);
    }
  };

  useEffect(() => {
    const selectedKey = state.selectedModel?.key;
    if (!selectedKey || loadingModels || !state.gatewayAlive) return;
    if (switchingModelKey) return;

    if (autoSwitchLockRef.current === selectedKey) return;
    if (modelStatus?.ready && modelStatus.model_key === selectedKey) {
      autoSwitchLockRef.current = selectedKey;
      return;
    }

    autoSwitchLockRef.current = selectedKey;
    void serveModelAndWait(selectedKey, true);
  }, [loadingModels, modelStatus?.model_key, modelStatus?.ready, serveModelAndWait, state.gatewayAlive, state.selectedModel, switchingModelKey]);

  const settingsInputClass =
    "h-9 rounded-lg border-border bg-surface-3 text-sm text-text-high placeholder:text-text-muted focus-visible:ring-primary focus-visible:ring-offset-0";

  const activeModelTitle = useMemo(() => {
    if (!modelStatus?.model_key) return null;
    return models.find((m) => m.key === modelStatus.model_key)?.title || modelStatus.model_key;
  }, [modelStatus?.model_key, models]);

  const runtimeBadge = (() => {
    if (switchingModelKey) {
      return {
        text: "Yükleniyor",
        cls: "border-warning/30 bg-warning/10 text-warning",
      };
    }
    if (modelStatus?.ready) {
      return {
        text: "Hazır",
        cls: "border-success/30 bg-success/10 text-success",
      };
    }
    if (modelStatus?.running) {
      return {
        text: "Başlatıldı",
        cls: "border-warning/30 bg-warning/10 text-warning",
      };
    }
    return {
      text: "Durduruldu",
      cls: "border-border bg-surface-3 text-text-dim",
    };
  })();

  return (
    <aside
      className={cn(
        "flex min-h-0 flex-col overflow-hidden rounded-2xl border border-border/80 bg-surface-1/90 shadow-[0_25px_60px_-48px_rgba(15,23,42,0.5)] backdrop-blur-sm",
        className
      )}
    >
      <div className="border-b border-border/70 px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-text-dim">Control Center</p>
            <h2 className="mt-1 text-base font-semibold text-text-high">Model ve Görev</h2>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-primary/25 bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary">
            <Sparkles className="h-3 w-3" />
            Live
          </span>
        </div>
      </div>

      {notice && (
        <div
          className={cn(
            "mx-4 mt-4 flex items-center gap-2 rounded-lg border px-3 py-2 text-xs",
            notice.type === "success"
              ? "border-success/35 bg-success/10 text-success"
              : "border-error/35 bg-error/10 text-error"
          )}
        >
          {notice.type === "success" ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : (
            <AlertCircle className="h-3.5 w-3.5" />
          )}
          <span>{notice.text}</span>
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="space-y-4 p-4">
          <Card className="border-border/70 bg-surface-2 shadow-none">
            <CardContent className="p-3">
              <div
                className={cn(
                  "flex items-center justify-between rounded-lg border px-3 py-2 text-xs font-medium",
                  state.gatewayAlive
                    ? "border-success/30 bg-success/10 text-success"
                    : "border-warning/30 bg-warning/10 text-warning"
                )}
              >
                <span>Gateway Durumu</span>
                <span>{state.gatewayAlive ? "Aktif" : "Bağlantı yok"}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-surface-2 shadow-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Model Runtime</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between rounded-lg border border-border/70 bg-surface-3 px-3 py-2">
                <div>
                  <p className="text-xs text-text-dim">Aktif model</p>
                  <p className="text-xs font-medium text-text-high">{activeModelTitle || "-"}</p>
                </div>
                <span className={cn("rounded-full border px-2 py-0.5 text-[11px] font-medium", runtimeBadge.cls)}>
                  {switchingModelKey && <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />}
                  {runtimeBadge.text}
                </span>
              </div>

              <div className="flex items-center justify-between text-[11px] text-text-dim">
                <span>PID: {modelStatus?.pid ?? "-"}</span>
                <span>Runtime: {modelStatus?.runtime || "-"}</span>
                <button
                  type="button"
                  className="inline-flex items-center gap-1 rounded-md border border-border bg-surface-3 px-2 py-1 text-text-dim transition-colors hover:text-text-high"
                  onClick={() => void refreshModelStatus()}
                  disabled={isRefreshingStatus}
                >
                  {isRefreshingStatus ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3 w-3" />
                  )}
                  Yenile
                </button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-surface-2 shadow-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Model Seçimi</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {loadingModels ? (
                <p className="rounded-lg bg-surface-3 px-3 py-2 text-sm text-text-muted">Modeller yükleniyor...</p>
              ) : modelError ? (
                <p className="rounded-lg border border-error/30 bg-error/10 px-3 py-2 text-sm text-error">
                  Hata: {modelError}
                </p>
              ) : (
                <>
                  <Select value={state.selectedModel?.key || ""} onValueChange={handleModelChange}>
                    <SelectTrigger className="h-10 rounded-lg border-border bg-surface-3 text-text-high focus:ring-primary">
                      <SelectValue placeholder="Model seçin" />
                    </SelectTrigger>
                    <SelectContent className="border-border bg-surface-1 text-text-high">
                      {models.map((model) => (
                        <SelectItem key={model.key} value={model.key}>
                          {model.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {state.selectedModel?.notes && <p className="text-xs leading-relaxed text-text-dim">{state.selectedModel.notes}</p>}
                </>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-surface-2 shadow-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Görev</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={state.selectedTask} onValueChange={handleTaskChange}>
                <SelectTrigger className="h-10 rounded-lg border-border bg-surface-3 text-text-high focus:ring-primary">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-border bg-surface-1 text-text-high">
                  {availableTasks.map((task) => (
                    <SelectItem key={task} value={task}>
                      {task.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="advanced" className="overflow-hidden rounded-xl border border-border/70 bg-surface-2">
              <AccordionTrigger className="px-4 py-3 text-sm font-medium text-text-high hover:no-underline hover:bg-surface-3/70">
                <span className="inline-flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Gelişmiş Ayarlar
                </span>
              </AccordionTrigger>
              <AccordionContent className="space-y-3 border-t border-border/70 px-4 py-4">
                <div>
                  <label className="mb-1 block text-xs text-text-dim">max_new_tokens</label>
                  <Input
                    type="number"
                    min={1}
                    max={4096}
                    className={settingsInputClass}
                    value={state.settings.maxNewTokens}
                    onChange={(e) => {
                      const value = parseInt(e.target.value, 10) || 1;
                      const clamped = Math.min(Math.max(value, 1), 4096);
                      dispatch({ type: "UPDATE_SETTINGS", payload: { maxNewTokens: clamped } });
                    }}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-dim">temperature</label>
                  <Input
                    type="number"
                    min={0}
                    max={1}
                    step={0.01}
                    className={settingsInputClass}
                    value={state.settings.temperature}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value) || 0;
                      const clamped = Math.min(Math.max(value, 0), 1);
                      dispatch({ type: "UPDATE_SETTINGS", payload: { temperature: clamped } });
                    }}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-dim">top_p</label>
                  <Input
                    type="number"
                    min={0}
                    max={1}
                    step={0.01}
                    className={settingsInputClass}
                    value={state.settings.topP}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value) || 0;
                      const clamped = Math.min(Math.max(value, 0), 1);
                      dispatch({ type: "UPDATE_SETTINGS", payload: { topP: clamped } });
                    }}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-dim">presence_penalty</label>
                  <Input
                    type="number"
                    min={-2}
                    max={2}
                    step={0.01}
                    className={settingsInputClass}
                    value={state.settings.presencePenalty}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value) || 0;
                      const clamped = Math.min(Math.max(value, -2), 2);
                      dispatch({ type: "UPDATE_SETTINGS", payload: { presencePenalty: clamped } });
                    }}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-dim">frequency_penalty</label>
                  <Input
                    type="number"
                    min={-2}
                    max={2}
                    step={0.01}
                    className={settingsInputClass}
                    value={state.settings.frequencyPenalty}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value) || 0;
                      const clamped = Math.min(Math.max(value, -2), 2);
                      dispatch({ type: "UPDATE_SETTINGS", payload: { frequencyPenalty: clamped } });
                    }}
                  />
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <Card className="border-border/70 bg-surface-2 shadow-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">Prompt Davranışı</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-border/60 bg-surface-3 px-3 py-2 text-sm text-text-high">
                <input
                  type="checkbox"
                  checked={state.settings.freeMode}
                  onChange={(e) => dispatch({ type: "UPDATE_SETTINGS", payload: { freeMode: e.target.checked } })}
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                />
                Serbest mod (şablon ekleme)
              </label>
              {(state.selectedTask === "ocr" || state.selectedTask === "detection") && (
                <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-border/60 bg-surface-3 px-3 py-2 text-sm text-text-high">
                  <input
                    type="checkbox"
                    checked={state.settings.jsonStrict}
                    onChange={(e) => dispatch({ type: "UPDATE_SETTINGS", payload: { jsonStrict: e.target.checked } })}
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  Yapısal JSON iste
                </label>
              )}
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={handleServeModel}
              disabled={!state.selectedModel || loadingModels || !!switchingModelKey}
              className="h-10 rounded-lg"
            >
              {switchingModelKey ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-1.5 h-4 w-4" />
              )}
              {switchingModelKey ? "Yükleniyor" : "Başlat"}
            </Button>
            <Button
              onClick={handleStopModel}
              disabled={!!switchingModelKey}
              variant="outline"
              className="h-10 rounded-lg border-border text-text-high"
            >
              <Square className="mr-1.5 h-4 w-4" />
              Durdur
            </Button>
          </div>
        </div>
      </ScrollArea>

      {state.currentThreadId && (
        <>
          <Separator className="bg-border/80" />
          <div className="space-y-2 p-4">
            <Button
              onClick={() => dispatch({ type: "CLEAR_THREAD_HISTORY", payload: state.currentThreadId! })}
              variant="outline"
              className="h-10 w-full rounded-lg border-border text-text-high"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Sohbeti Sıfırla
            </Button>
            <Button onClick={() => dispatch({ type: "CLEAR_ALL_THREADS" })} variant="destructive" className="h-10 w-full rounded-lg">
              <Trash2 className="mr-2 h-4 w-4" />
              Tümünü Temizle
            </Button>
          </div>
        </>
      )}
    </aside>
  );
}
