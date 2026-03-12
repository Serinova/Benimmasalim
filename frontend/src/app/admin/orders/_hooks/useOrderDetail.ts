"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import type { OrderDetail, BackCoverConfig } from "../_lib/types";
import {
  fetchOrderDetail,
  fetchBackCoverConfig as fetchBackCoverConfigApi,
} from "../_lib/adminOrdersApi";

export function useOrderDetail() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<OrderDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [backCoverConfig, setBackCoverConfig] = useState<BackCoverConfig | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const pollTickRef = useRef(0);

  const loadDetail = useCallback(async (id: string) => {
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    try {
      const data = await fetchOrderDetail(id, controller.signal);
      if (!controller.signal.aborted) {
        setDetail(data);
        setLoading(false);
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  const selectOrder = useCallback((id: string) => {
    if (id === selectedId) return;
    setSelectedId(id);
    setDetail(null);
    pollTickRef.current = 0;
    loadDetail(id);
  }, [selectedId, loadDetail]);

  const closeDetail = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    setSelectedId(null);
    setDetail(null);
    pollTickRef.current = 0;
  }, []);

  const refreshDetail = useCallback(() => {
    if (selectedId) loadDetail(selectedId);
  }, [selectedId, loadDetail]);

  const updateDetailLocal = useCallback((updater: (prev: OrderDetail | null) => OrderDetail | null) => {
    setDetail(updater);
  }, []);

  // Back cover config (loaded once)
  useEffect(() => {
    fetchBackCoverConfigApi().then(setBackCoverConfig);
  }, []);

  // Polling for PROCESSING or incomplete CONFIRMED
  useEffect(() => {
    if (!selectedId || !detail) return;
    const isProcessing = detail.status === "PROCESSING";
    const pageCount = detail.page_count ?? 0;
    const imageCount = detail.page_images ? Object.keys(detail.page_images).length : 0;
    const isIncompleteConfirmed =
      detail.status === "CONFIRMED" && pageCount > 0 && imageCount < pageCount;

    if (!isProcessing && !isIncompleteConfirmed) {
      pollTickRef.current = 0;
      return;
    }

    const BACKOFF = [5000, 10000, 15000, 30000];
    const delay = BACKOFF[Math.min(pollTickRef.current, BACKOFF.length - 1)];
    const timer = setTimeout(async () => {
      try {
        await loadDetail(selectedId);
      } catch { /* silent */ }
      pollTickRef.current += 1;
    }, delay);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, detail?.status, detail?.page_count, detail?.page_images, loadDetail]);

  return {
    selectedId,
    detail,
    loading,
    backCoverConfig,
    selectOrder,
    closeDetail,
    refreshDetail,
    updateDetailLocal,
  };
}
