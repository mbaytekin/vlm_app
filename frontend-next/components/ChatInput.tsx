/**
 * ChatInput Component
 * Prompt composer with quick actions
 */

"use client";

import React, { KeyboardEvent, useMemo, useRef, useState } from "react";
import { Loader2, Mic, MessageSquareText, Send, X } from "lucide-react";

import { useApp } from "@/lib/app-context";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import { ImageUpload } from "./ImageUpload";

export function ChatInput() {
  const { createThread, dispatch, sendMessage, state } = useApp();
  const [input, setInput] = useState("");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const quickPrompts = useMemo(() => {
    const prompts = {
      caption: ["Bu sahneyi detaylı anlat.", "Görselde en dikkat çekici ögeler neler?"],
      vqa: ["Bu görselde kaç kişi var?", "Bu görselin ana konusu nedir?"],
      ocr: ["Tüm metni satır satır çıkar.", "Başlık ve alt başlıkları ayır."],
      detection: ["Nesneleri etiket ve koordinatla ver.", "Sadece büyük nesneleri tespit et."],
    };
    return prompts[state.selectedTask];
  }, [state.selectedTask]);

  const handleSubmit = async () => {
    if (!input.trim() || !state.currentThreadId || state.isLoading) return;

    const prompt = input.trim();
    setInput("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const currentAudio = audioFile || undefined;
    setAudioFile(null);
    if (audioInputRef.current) {
      audioInputRef.current.value = "";
    }
    await sendMessage(prompt, currentAudio);
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 220)}px`;
  };

  const handleAudioChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (!file) return;
    if (!file.type.startsWith("audio/")) {
      dispatch({ type: "SET_ERROR", payload: "Lütfen geçerli bir ses dosyası seçin." });
      e.target.value = "";
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      dispatch({ type: "SET_ERROR", payload: "Ses dosyası 25 MB sınırını aşıyor." });
      e.target.value = "";
      return;
    }
    dispatch({ type: "SET_ERROR", payload: null });
    setAudioFile(file);
  };

  const clearAudio = () => {
    setAudioFile(null);
    if (audioInputRef.current) {
      audioInputRef.current.value = "";
    }
  };

  if (!state.currentThreadId) {
    return (
      <div className="border-t border-border/70 bg-surface-1/95 px-4 py-4">
        <div className="mx-auto max-w-4xl text-center">
          <p className="mb-3 text-sm text-text-dim">Görsel yükleyerek veya metin sohbeti başlatarak devam edin.</p>
          <div className="flex flex-wrap justify-center gap-2">
            <ImageUpload compact={false} />
            <Button
              variant="outline"
              className="h-11 rounded-xl px-4"
              disabled={state.isLoading}
              onClick={() => void createThread()}
            >
              <MessageSquareText className="mr-2 h-4 w-4" />
              Metin Sohbeti Başlat
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-border/70 bg-surface-1/95 px-3 pb-4 pt-3 sm:px-5">
      <div className="mx-auto w-full max-w-4xl">
        <div className="mb-2 flex flex-wrap gap-2">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="rounded-full border border-border bg-surface-2 px-3 py-1 text-xs text-text-dim transition-colors hover:border-accent-1/40 hover:text-text-high"
              onClick={() => setInput(prompt)}
              disabled={state.isLoading}
            >
              {prompt}
            </button>
          ))}
        </div>
        {audioFile && (
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-border bg-surface-2 px-3 py-1 text-xs text-text-high">
            <Mic className="h-3.5 w-3.5" />
            <span className="max-w-[200px] truncate">{audioFile.name}</span>
            <button
              type="button"
              className="rounded-md p-0.5 text-text-dim transition-colors hover:bg-surface-3 hover:text-text-high"
              onClick={clearAudio}
              aria-label="Ses dosyasını kaldır"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        <div className="flex items-end gap-2 rounded-2xl border border-border bg-surface-2/90 p-2 shadow-[0_15px_35px_-30px_rgba(15,23,42,0.5)]">
          <ImageUpload compact />
          <input
            ref={audioInputRef}
            type="file"
            accept="audio/*"
            className="hidden"
            onChange={handleAudioChange}
            disabled={state.isLoading}
          />
          <Button
            variant="outline"
            size="icon"
            className="h-10 w-10 rounded-xl border-border text-text-high hover:bg-surface-3"
            disabled={state.isLoading}
            onClick={() => audioInputRef.current?.click()}
            title="Ses dosyası ekle"
          >
            <Mic className="h-4 w-4" />
          </Button>

          <div className="relative flex-1">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
              placeholder="Sorunuzu yazın... (Enter gönderir, Shift+Enter yeni satır)"
              disabled={state.isLoading}
              rows={1}
              className={cn(
                "min-h-[52px] max-h-[220px] resize-none rounded-xl border-0 bg-surface-2 text-text-high shadow-none ring-0",
                "placeholder:text-text-muted focus-visible:ring-0 focus-visible:ring-offset-0",
                "pr-12"
              )}
            />
            <Button
              onClick={handleSubmit}
              disabled={!input.trim() || state.isLoading}
              size="icon"
              className="absolute bottom-2 right-2 h-8 w-8 rounded-lg"
              aria-label="Mesaj gönder"
            >
              {state.isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
