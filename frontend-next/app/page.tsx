/**
 * Main Page
 * Modern, responsive VLM workspace
 */

"use client";

import React from "react";
import { AlertTriangle, Wifi, WifiOff, X } from "lucide-react";

import { Sidebar } from "@/components/Sidebar";
import { ChatArea } from "@/components/ChatArea";
import { ChatInput } from "@/components/ChatInput";
import { useApp } from "@/lib/app-context";
import { cn } from "@/lib/utils";

export default function HomePage() {
  const { state, dispatch } = useApp();

  return (
    <div className="relative min-h-screen overflow-hidden bg-base-bg text-text-high">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_8%_12%,rgba(21,94,239,0.15),transparent_34%),radial-gradient(circle_at_92%_0%,rgba(15,118,110,0.16),transparent_30%)]" />

      <div className="relative z-10 mx-auto max-w-[1800px] p-3 sm:p-4 lg:p-6">
        <header className="mb-3 rounded-2xl border border-border/80 bg-surface-1/90 px-4 py-3 shadow-[0_12px_35px_-28px_rgba(15,23,42,0.5)] backdrop-blur-sm sm:px-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-text-dim">
                Visual Intelligence Workspace
              </p>
              <h1 className="text-lg font-semibold text-text-high sm:text-xl">
                VLM Gateway Console
              </h1>
            </div>
            <div
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium",
                state.gatewayAlive
                  ? "border-success/35 bg-success/10 text-success"
                  : "border-warning/35 bg-warning/10 text-warning"
              )}
            >
              {state.gatewayAlive ? (
                <Wifi className="h-3.5 w-3.5" />
              ) : (
                <WifiOff className="h-3.5 w-3.5" />
              )}
              {state.gatewayAlive ? "Gateway Online" : "Gateway Offline"}
            </div>
          </div>
        </header>

        {state.error && (
          <div className="mb-3 flex items-start gap-3 rounded-xl border border-error/35 bg-error/10 px-4 py-3 text-sm shadow-sm">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-error" />
            <p className="flex-1 text-text-high">{state.error}</p>
            <button
              type="button"
              onClick={() => dispatch({ type: "SET_ERROR", payload: null })}
              className="rounded-md p-1 text-text-dim transition-colors hover:bg-surface-3 hover:text-text-high"
              aria-label="Hata mesajını kapat"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="grid gap-3 lg:grid-cols-[minmax(300px,360px)_minmax(0,1fr)]">
          <Sidebar className="h-[36svh] min-h-[360px] lg:h-[calc(100svh-11.5rem)]" />

          <section className="min-h-0 rounded-2xl border border-border/80 bg-surface-1/90 shadow-[0_28px_70px_-50px_rgba(15,23,42,0.55)] backdrop-blur-sm">
            <div className="flex h-[58svh] min-h-[420px] flex-col lg:h-[calc(100svh-11.5rem)]">
              <ChatArea />
              <ChatInput />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
