/**
 * MessageBubble Component
 * Chat message renderer
 */

"use client";

import React from "react";
import { ChevronDown } from "lucide-react";

import { ChatMessage } from "@/types/state";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const timestamp = new Date(message.timestamp).toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div className="max-w-[92%] sm:max-w-[84%]">
        <div className={cn("mb-1 flex items-center gap-2 text-[11px]", isUser ? "justify-end text-text-dim" : "justify-start text-text-muted")}>
          <span className={cn("rounded-full px-2 py-0.5 font-medium", isUser ? "bg-primary/15 text-primary" : "bg-surface-3 text-text-dim")}>
            {isUser ? "Sen" : "Asistan"}
          </span>
          <span>{timestamp}</span>
        </div>

        <article
          className={cn(
            "rounded-2xl border px-4 py-3 text-sm leading-relaxed shadow-[0_14px_35px_-30px_rgba(15,23,42,0.55)]",
            isUser
              ? "border-primary/30 bg-primary text-primary-foreground"
              : "border-border/75 bg-surface-2 text-text-high"
          )}
        >
          <div className="whitespace-pre-wrap break-words">{message.text}</div>

          {message.render && (
            <div className="mt-3 space-y-2">
              {message.render.annotated_png_b64 && (
                <div className="overflow-hidden rounded-xl border border-border/75 bg-surface-3">
                  <img
                    src={`data:image/png;base64,${message.render.annotated_png_b64}`}
                    alt="Annotated image"
                    className="h-auto w-full"
                  />
                  <div className="border-t border-border/70 px-3 py-2 text-xs text-text-muted">Algılanan kutular</div>
                </div>
              )}

              {message.render.boxes && message.render.boxes.length > 0 && (
                <details className="rounded-xl border border-border/70 bg-surface-3 px-3 py-2">
                  <summary className="flex cursor-pointer items-center gap-2 text-xs text-text-dim transition-colors hover:text-text-high">
                    <ChevronDown className="h-3 w-3" />
                    Boxes ({message.render.boxes.length})
                  </summary>
                  <pre className="mt-2 overflow-auto rounded-lg bg-surface-1 p-2 text-xs text-text-dim">
                    {JSON.stringify(message.render.boxes, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </article>
      </div>
    </div>
  );
}
