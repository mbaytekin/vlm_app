/**
 * ImageViewer Component
 * Büyütülmüş görsel görüntüleyici modal
 * Görsele tıklayınca açılır, boş alana tıklayınca kapanır
 */

"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageViewerProps {
  imageUrl: string | null;
  isOpen: boolean;
  onClose: () => void;
  alt?: string;
}

export function ImageViewer({ imageUrl, isOpen, onClose, alt = "Görsel" }: ImageViewerProps) {
  if (!imageUrl) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent 
        className="max-w-[95vw] max-h-[95vh] w-auto h-auto p-0 bg-transparent border-0 shadow-none [&>button]:hidden"
        onPointerDownOutside={onClose}
        onEscapeKeyDown={onClose}
      >
        <div 
          className="relative w-full h-full flex items-center justify-center p-4"
          onClick={(e) => {
            // Container'a tıklanınca kapat, ama görsele tıklanınca kapatma
            if (e.target === e.currentTarget) {
              onClose();
            }
          }}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className={cn(
              "absolute top-6 right-6 z-50",
              "w-10 h-10 rounded-full bg-surface-2/90 backdrop-blur-sm",
              "border border-border",
              "flex items-center justify-center",
              "text-text-high hover:text-text-high",
              "hover:bg-surface-3 transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-primary",
              "shadow-lg cursor-pointer"
            )}
            aria-label="Kapat"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Image */}
          <img
            src={imageUrl}
            alt={alt}
            className="max-w-full max-h-[90vh] w-auto h-auto object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()} // Görsele tıklanınca modal kapanmasın
            draggable={false}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}

