"use client";

import React, { forwardRef, useRef } from "react";
import { motion } from "framer-motion";
import { BookOpen } from "lucide-react";
import HTMLFlipBook from "react-pageflip";

// ============ PAGE COMPONENT FOR FLIPBOOK ============
const FlipBookPage = forwardRef<HTMLDivElement, { imageUrl: string; pageNumber: number }>(
  ({ imageUrl, pageNumber }, ref) => {
    return (
      <div ref={ref} className="h-full w-full bg-white shadow-md">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={`Sayfa ${pageNumber}`}
            className="h-full w-full object-cover"
            draggable={false}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-amber-50 to-amber-100">
            <div className="text-center text-amber-400">
              <BookOpen className="mx-auto mb-2 h-8 w-8 opacity-50" />
              <p className="text-xs">Sayfa {pageNumber + 1}</p>
            </div>
          </div>
        )}
      </div>
    );
  }
);
FlipBookPage.displayName = "FlipBookPage";

// ============ FLIPBOOK PREVIEW ============
interface FlipbookPreviewProps {
  images: string[];
  width: number;
  height: number;
  bookThickness: number;
}

export function FlipbookPreview({ images, width, height, bookThickness }: FlipbookPreviewProps) {
  const bookRef = useRef<HTMLDivElement | null>(null);
  const isLandscape = width > height;

  // Calculate display dimensions (max 400px width)
  const maxWidth = 350;
  const scale = maxWidth / width;
  const displayWidth = Math.round(width * scale);
  const displayHeight = Math.round(height * scale);

  // Ensure we have at least 4 pages for the flipbook
  const pageImages =
    images.length > 0
      ? [...images, ...Array(Math.max(0, 4 - images.length)).fill("")]
      : ["", "", "", ""];

  return (
    <div className="relative">
      {/* Book shadow */}
      <div
        className="absolute -bottom-4 left-1/2 -translate-x-1/2 rounded-[50%] opacity-40"
        style={{
          width: displayWidth * 1.8,
          height: 20,
          background: "radial-gradient(ellipse at center, rgba(0,0,0,0.5) 0%, transparent 70%)",
          filter: "blur(4px)",
        }}
      />

      {/* Book container with 3D effect */}
      <div
        className="relative mx-auto"
        style={{
          perspective: "1500px",
          transformStyle: "preserve-3d",
        }}
      >
        {/* Book spine effect */}
        <div
          className="absolute left-1/2 top-0 z-10 -translate-x-1/2 rounded-sm bg-gradient-to-r from-amber-900 via-amber-800 to-amber-900"
          style={{
            width: bookThickness * 3,
            height: displayHeight,
            transform: `translateZ(-${bookThickness}px)`,
            boxShadow: "inset 0 0 10px rgba(0,0,0,0.3)",
          }}
        />

        {/* Flipbook */}
        <div
          className="relative overflow-hidden rounded-lg bg-white"
          style={{
            boxShadow: `
              0 ${bookThickness}px ${bookThickness * 2}px rgba(0,0,0,0.15),
              0 4px 6px rgba(0,0,0,0.1),
              inset 0 0 0 1px rgba(0,0,0,0.05)
            `,
          }}
        >
          <HTMLFlipBook
            ref={bookRef}
            width={displayWidth / 2}
            height={displayHeight}
            size="fixed"
            minWidth={displayWidth / 2}
            maxWidth={displayWidth / 2}
            minHeight={displayHeight}
            maxHeight={displayHeight}
            showCover={true}
            mobileScrollSupport={true}
            className="flipbook-preview"
            style={{}}
            startPage={0}
            drawShadow={true}
            flippingTime={600}
            usePortrait={!isLandscape}
            startZIndex={0}
            autoSize={false}
            maxShadowOpacity={0.4}
            showPageCorners={true}
            disableFlipByClick={false}
            swipeDistance={20}
            clickEventForward={true}
            useMouseEvents={true}
          >
            {pageImages.map((img, idx) => (
              <FlipBookPage key={idx} imageUrl={img} pageNumber={idx} />
            ))}
          </HTMLFlipBook>
        </div>
      </div>

      {/* Instructions */}
      {images.length > 0 && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 text-center text-xs text-gray-400"
        >
          Sayfaları çevirmek için tıklayın veya sürükleyin
        </motion.p>
      )}
    </div>
  );
}
