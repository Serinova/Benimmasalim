"use client";

import { useRef, useState, useEffect } from "react";

interface LazyImageProps {
  readonly src: string;
  readonly alt: string;
  readonly className?: string;
}

export function LazyImage({ src, alt, className }: LazyImageProps) {
  const imgRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    setIsVisible(false);
    setLoaded(false);
    setError(false);

    const el = imgRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [src]);

  return (
    <div ref={imgRef} className={`relative ${className ?? ""}`}>
      {!loaded && !error && (
        <div className="absolute inset-0 flex items-center justify-center rounded bg-slate-100">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-violet-500" />
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center rounded bg-slate-100">
          <span className="text-xs text-slate-400">Yüklenemedi</span>
        </div>
      )}
      {isVisible && (
        <img
          key={src}
          src={src}
          alt={alt}
          className={`h-full w-full rounded object-cover ${loaded ? "opacity-100" : "opacity-0"} transition-opacity duration-300`}
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
        />
      )}
    </div>
  );
}
