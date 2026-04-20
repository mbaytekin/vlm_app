/**
 * ImageUpload Component
 * Image upload trigger
 */

"use client";

import React, { useRef, useState } from "react";
import { useApp } from "@/lib/app-context";
import { Button } from "@/components/ui/button";
import { ImageIcon, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageUploadProps {
  compact?: boolean;
  className?: string;
}

const MAX_UPLOAD_SIZE_MB = 15;

export function ImageUpload({ compact = true, className }: ImageUploadProps) {
  const { createThread, state, dispatch } = useApp();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      dispatch({
        type: "SET_ERROR",
        payload: "Lütfen PNG veya JPEG formatında bir görsel seçin.",
      });
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    if (file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024) {
      dispatch({
        type: "SET_ERROR",
        payload: `Dosya boyutu ${MAX_UPLOAD_SIZE_MB} MB sınırını aşıyor.`,
      });
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    setIsUploading(true);
    dispatch({ type: "SET_ERROR", payload: null });
    try {
      await createThread(file);
    } catch (error) {
      console.error("Upload error:", error);
      dispatch({
        type: "SET_ERROR",
        payload: `Görsel yüklenemedi: ${(error as Error).message}`,
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg"
        onChange={handleFileChange}
        disabled={isUploading || state.isLoading}
        className="hidden"
        id="image-upload"
      />
      <Button
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading || state.isLoading}
        variant="outline"
        size={compact ? "icon" : "default"}
        className={cn(
          "border-border text-text-high hover:bg-surface-3",
          "disabled:cursor-not-allowed disabled:opacity-50",
          compact ? "h-10 w-10 rounded-xl" : "h-11 rounded-xl px-4",
          className
        )}
        title="Görsel yükle"
      >
        {isUploading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <>
            <ImageIcon className="h-4 w-4" />
            {!compact && <span className="text-sm font-medium">Görsel Yükle</span>}
          </>
        )}
      </Button>
    </>
  );
}
