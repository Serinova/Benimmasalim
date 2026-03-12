"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import type { OrderDetail } from "../_lib/types";
import * as api from "../_lib/adminOrdersApi";
import JSZip from "jszip";

interface UseOrderActionsParams {
  detail: OrderDetail | null;
  refreshDetail: () => void;
  refreshList: () => void;
  updateDetailLocal: (updater: (prev: OrderDetail | null) => OrderDetail | null) => void;
}

export function useOrderActions({
  detail,
  refreshDetail,
  refreshList,
  updateDetailLocal,
}: UseOrderActionsParams) {
  const router = useRouter();
  const { toast } = useToast();
  const [pdfDownloading, setPdfDownloading] = useState(false);
  const [zipDownloading, setZipDownloading] = useState(false);
  const [bookGenerating, setBookGenerating] = useState(false);
  const [coloringGenerating, setColoringGenerating] = useState(false);

  const handleAuthExpired = useCallback(() => {
    toast({ title: "Oturum süresi doldu", description: "Lütfen tekrar giriş yapın.", variant: "destructive" });
    localStorage.removeItem("token");
    router.push("/auth/login");
  }, [toast, router]);

  const updateStatus = useCallback(async (id: string, newStatus: string) => {
    try {
      await api.updateOrderStatus(id, newStatus);
      toast({ title: "Başarılı", description: `Durum ${newStatus} olarak güncellendi` });
      refreshList();
      refreshDetail();
    } catch (err) {
      toast({ title: "Hata", description: err instanceof Error ? err.message : "Güncelleme başarısız", variant: "destructive" });
    }
  }, [toast, refreshList, refreshDetail]);

  const handleGenerateBook = useCallback(async (previewId: string) => {
    if (bookGenerating) return;
    setBookGenerating(true);
    try {
      toast({ title: "Kitap oluşturuluyor...", description: "Bu işlem birkaç dakika sürebilir. Lütfen bekleyin." });
      const data = await api.generateBook(previewId);
      if (data.pdf_url) {
        updateDetailLocal(prev => prev ? { ...prev, pdf_url: data.pdf_url } : prev);
        toast({ title: "✅ Kitap Hazır!", description: "PDF indirme bağlantısı açılıyor..." });
        window.open(data.pdf_url, "_blank");
      } else if (data.pdf_error) {
        toast({ title: "PDF oluşturulamadı", description: `Hata: ${data.pdf_error}`, variant: "destructive" });
      } else {
        toast({ title: "Kitap oluşturuldu", description: "PDF oluşturulurken sorun oluştu, tekrar deneyin.", variant: "destructive" });
      }
      refreshDetail();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_EXPIRED") {
        handleAuthExpired();
        return;
      }
      toast({ title: "Hata", description: err instanceof Error ? err.message : "Kitap oluşturma başarısız", variant: "destructive" });
    } finally {
      setBookGenerating(false);
    }
  }, [bookGenerating, toast, refreshDetail, updateDetailLocal, handleAuthExpired]);

  const handleDownloadPdf = useCallback(async () => {
    if (!detail || pdfDownloading) return;
    setPdfDownloading(true);
    try {
      let pdfUrl = detail.pdf_url ?? null;
      if (!pdfUrl) {
        toast({ title: "PDF aranıyor...", description: "Lütfen bekleyin." });
        pdfUrl = await api.downloadPdfUrl(detail.id);
      }
      if (!pdfUrl) throw new Error("PDF URL alınamadı");

      toast({ title: "PDF indiriliyor...", description: "Lütfen bekleyin." });
      const pdfRes = await fetch(pdfUrl);
      if (!pdfRes.ok) throw new Error("PDF dosyası indirilemedi");
      const blob = await pdfRes.blob();
      const sizeMb = (blob.size / 1024 / 1024).toFixed(1);
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `kitap_${detail.child_name || detail.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(downloadUrl);
      updateDetailLocal(prev => prev ? { ...prev, pdf_url: pdfUrl } : prev);
      toast({ title: "PDF indirildi!", description: `${sizeMb} MB` });
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_EXPIRED") {
        handleAuthExpired();
        return;
      }
      toast({ title: "Hata", description: err instanceof Error ? err.message : "PDF indirilemedi", variant: "destructive" });
    } finally {
      setPdfDownloading(false);
    }
  }, [detail, pdfDownloading, toast, updateDetailLocal, handleAuthExpired]);

  const handleGenerateRemaining = useCallback(async (previewId: string, missingCount: number) => {
    try {
      const data = await api.generateRemainingPages(previewId);
      toast({ title: "Başarılı", description: data.message || `${missingCount} eksik sayfa oluşturuluyor...` });
    } catch {
      toast({ title: "Hata", description: "Bağlantı hatası", variant: "destructive" });
    }
  }, [toast]);

  const handleRecompose = useCallback(async (previewId: string) => {
    try {
      const updated = await api.recomposeImages(previewId);
      updateDetailLocal(() => updated);
      toast({ title: "Başarılı", description: "Kapak güncel template ile yeniden compose edildi." });
    } catch {
      toast({ title: "Hata", description: "Bağlantı hatası", variant: "destructive" });
    }
  }, [toast, updateDetailLocal]);

  const handleColoringBook = useCallback(async (previewId: string, existingUrl?: string | null) => {
    if (existingUrl) {
      window.open(existingUrl, "_blank");
      toast({ title: "Açılıyor", description: "Boyama Kitabı PDF'i yeni sekmede açılıyor." });
      return;
    }
    if (coloringGenerating) return;
    setColoringGenerating(true);
    toast({ title: "Başlatılıyor...", description: "Boyama kitabı üretimi başlatılıyor. Lütfen bekleyin." });
    try {
      const data = await api.generateColoringBook(previewId);
      if (data.coloring_pdf_url) {
        window.open(data.coloring_pdf_url, "_blank");
        updateDetailLocal(prev => prev ? { ...prev, coloring_pdf_url: data.coloring_pdf_url } : prev);
        toast({ title: "✅ Boyama Kitabı Hazır!", description: "PDF yeni sekmede açılıyor." });
      } else {
        toast({ title: "Başlatıldı", description: data.message || "Arka planda üretiliyor, birkaç dakika bekleyin." });
      }
    } catch (err) {
      toast({ title: "Hata", description: err instanceof Error ? err.message : "Sunucuya bağlanılamadı", variant: "destructive" });
    } finally {
      setColoringGenerating(false);
    }
  }, [coloringGenerating, toast, updateDetailLocal]);

  const handleInvoiceAction = useCallback(async (
    orderId: string,
    action: string,
    method: string = "POST",
    successMsg?: string,
  ) => {
    try {
      const data = await api.invoiceAction(orderId, action, method);
      toast({ title: "Başarılı", description: successMsg || JSON.stringify(data).slice(0, 100) });
      refreshDetail();
    } catch (err) {
      toast({ title: "Hata", description: err instanceof Error ? err.message : "İşlem başarısız", variant: "destructive" });
    }
  }, [toast, refreshDetail]);

  const handleDownloadInvoicePdf = useCallback(async (orderId: string, invoiceNumber: string) => {
    try {
      await api.downloadInvoicePdf(orderId, invoiceNumber);
    } catch {
      toast({ title: "Hata", description: "Fatura PDF indirilemedi", variant: "destructive" });
    }
  }, [toast]);

  const handleCreateInvoice = useCallback(async (orderId: string) => {
    try {
      toast({ title: "Fatura oluşturuluyor...", description: "Lütfen bekleyin." });
      const data = await api.createInvoice(orderId);
      toast({ title: "Fatura oluşturuldu", description: `Fatura No: ${data.invoice_number ?? ""}` });
      refreshDetail();
    } catch (err) {
      toast({ title: "Fatura oluşturulamadı", description: err instanceof Error ? err.message : "Sunucu hatası", variant: "destructive" });
    }
  }, [toast, refreshDetail]);

  const downloadSingleImage = useCallback(async (url: string, filename: string) => {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error("Resim indirilemedi");
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch {
      toast({ title: "Hata", description: `"${filename}" indirilemedi`, variant: "destructive" });
    }
  }, [toast]);

  const downloadAllImages = useCallback(async () => {
    if (!detail?.page_images || zipDownloading) return;
    setZipDownloading(true);
    const childName = (detail.child_name || "kitap").replace(/\s+/g, "_");
    const zipFilename = `${childName}_gorseller.zip`;
    try {
      const zip = new JSZip();
      const entries = Object.entries(detail.page_images).sort(([a], [b]) => {
        const order = (k: string) => {
          if (k === "dedication") return -2;
          if (k === "intro") return -1;
          return parseInt(k) || 0;
        };
        return order(a) - order(b);
      });
      if (detail.back_cover_image_url) entries.push(["back_cover", detail.back_cover_image_url]);

      let downloaded = 0;
      toast({ title: "Resimler indiriliyor...", description: `0 / ${entries.length} tamamlandı` });
      for (const [pageKey, url] of entries) {
        try {
          const res = await fetch(url);
          if (!res.ok) continue;
          const blob = await res.blob();
          const ext = blob.type.includes("png") ? "png" : "jpg";
          const name =
            pageKey === "dedication" ? `00_karsilama_1.${ext}` :
            pageKey === "intro" ? `01_karsilama_2.${ext}` :
            pageKey === "back_cover" ? `99_arka_kapak.${ext}` :
            `${String(parseInt(pageKey) + 2).padStart(2, "0")}_sayfa.${ext}`;
          zip.file(name, blob);
          downloaded++;
        } catch { /* skip */ }
      }
      if (downloaded === 0) {
        toast({ title: "Hata", description: "Hiçbir resim indirilemedi", variant: "destructive" });
        return;
      }
      const zipBlob = await zip.generateAsync({ type: "blob" });
      const blobUrl = URL.createObjectURL(zipBlob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = zipFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
      toast({ title: "Tamamlandı", description: `${downloaded} resim ZIP olarak indirildi` });
    } catch {
      toast({ title: "Hata", description: "ZIP oluşturulamadı", variant: "destructive" });
    } finally {
      setZipDownloading(false);
    }
  }, [detail, zipDownloading, toast]);

  return {
    pdfDownloading,
    zipDownloading,
    bookGenerating,
    coloringGenerating,
    updateStatus,
    handleGenerateBook,
    handleDownloadPdf,
    handleGenerateRemaining,
    handleRecompose,
    handleColoringBook,
    handleInvoiceAction,
    handleDownloadInvoicePdf,
    handleCreateInvoice,
    downloadSingleImage,
    downloadAllImages,
  };
}
