/**
 * ChatArea Component
 * Main conversation canvas
 */

"use client";

import React, { useEffect, useRef, useState } from "react";
import { Camera, ImageIcon, MessageSquareText } from "lucide-react";

import { useApp } from "@/lib/app-context";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

import { ImageUpload } from "./ImageUpload";
import { ImageViewer } from "./ImageViewer";
import { MessageBubble } from "./MessageBubble";

export function ChatArea() {
  const { createThread, state } = useApp();
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [imageViewerOpen, setImageViewerOpen] = useState(false);
  const currentThread = state.currentThreadId ? state.threads[state.currentThreadId] : null;

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [currentThread?.history]);

  if (!currentThread) {
    return (
      <div className="flex flex-1 items-center justify-center px-4 py-8">
        <div className="w-full max-w-lg rounded-2xl border border-border/80 bg-surface-2/80 p-8 text-center shadow-[0_20px_45px_-38px_rgba(15,23,42,0.55)]">
          <div className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-subtle-2 text-accent-1">
            <ImageIcon className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-semibold text-text-high">Sohbete görselle veya metinle başlayın</h3>
          <p className="mt-2 text-sm leading-relaxed text-text-dim">
            Görsel tabanlı analiz yapabilir veya resim yüklemeden doğrudan metin sohbeti açabilirsiniz.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
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

  const sortedMessages = [...currentThread.history].sort((a, b) => a.timestamp - b.timestamp);
  const createdAtText = new Date(currentThread.created_at).toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <ScrollArea className="flex-1">
      <div className="mx-auto flex w-full max-w-4xl flex-col px-3 pb-6 pt-4 sm:px-5">
        {currentThread.preview_dataurl && (
          <Card className="mb-5 border-border/70 bg-surface-2/85 p-4 shadow-none">
            <div className="flex flex-wrap items-start gap-4">
              <button
                type="button"
                className="group relative overflow-hidden rounded-xl border border-border/80"
                onClick={() => setImageViewerOpen(true)}
                title="Görseli büyüt"
              >
                <img
                  src={currentThread.preview_dataurl}
                  alt="Aktif görsel"
                  className={cn(
                    "h-28 w-28 object-cover transition-transform duration-200",
                    "group-hover:scale-[1.03]"
                  )}
                />
                <span className="absolute inset-x-0 bottom-0 inline-flex items-center justify-center gap-1 bg-black/55 px-2 py-1 text-[10px] text-white opacity-0 transition-opacity group-hover:opacity-100">
                  <Camera className="h-3 w-3" />
                  Büyüt
                </span>
              </button>

              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-semibold text-text-high">Aktif görsel hazır</h3>
                <p className="mt-1 text-xs leading-relaxed text-text-dim">
                  Mevcut sohbetteki tüm mesajlar bu görsele bağlıdır. Sohbeti sürdürmek için doğrudan mesaj gönderin.
                </p>
                <p className="mt-3 text-[11px] text-text-muted">
                  Thread oluşturma zamanı: {createdAtText}
                </p>
              </div>
            </div>
          </Card>
        )}

        {currentThread.preview_dataurl && (
          <ImageViewer
            imageUrl={currentThread.preview_dataurl}
            isOpen={imageViewerOpen}
            onClose={() => setImageViewerOpen(false)}
            alt="Aktif görsel"
          />
        )}

        <div className="flex-1 space-y-4">
          {sortedMessages.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border bg-surface-2/70 px-5 py-6 text-center">
              <p className="text-sm font-medium text-text-high">Henüz mesaj yok</p>
              <p className="mt-1 text-sm text-text-dim">İlk sorunuzu yazarak analizi başlatın.</p>
            </div>
          ) : (
            sortedMessages.map((message) => <MessageBubble key={message.id} message={message} />)
          )}
        </div>
        <div ref={chatEndRef} />
      </div>
    </ScrollArea>
  );
}
