"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getOrderDetail,
  deletePhotoNow,
  getUserProfile,
  API_BASE_URL,
  type OrderDetail,
  type InvoiceSummary,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import {
  ArrowLeft,
  Package,
  Truck,
  CheckCircle,
  Clock,
  Download,
  Headphones,
  QrCode,
  ExternalLink,
  MessageCircle,
  Mail,
  AlertCircle,
  Loader2,
  Shield,
  Trash2,
  RefreshCw,
  FileText,
  XCircle,
} from "lucide-react";

// ─── Constants ────────────────────────────────────────────────────

const TIMELINE_STEPS = [
  { key: "PAID", label: "Ödendi", icon: CheckCircle },
  { key: "PROCESSING", label: "Üretiliyor", icon: Loader2 },
  { key: "READY_FOR_PRINT", label: "Baskıya Hazır", icon: Package },
  { key: "SHIPPED", label: "Kargoda", icon: Truck },
  { key: "DELIVERED", label: "Teslim Edildi", icon: CheckCircle },
] as const;

const STATUS_ORDER = [
  "DRAFT",
  "TEXT_APPROVED",
  "COVER_APPROVED",
  "PAYMENT_PENDING",
  "PAID",
  "PROCESSING",
  "READY_FOR_PRINT",
  "SHIPPED",
  "DELIVERED",
];

const CARRIER_URLS: Record<string, (tn: string) => string> = {
  yurtici: (tn) =>
    `https://www.yurticikargo.com/tr/online-servisler/gonderi-sorgula?code=${tn}`,
  aras: (tn) =>
    `https://www.araskargo.com.tr/taki.aspx?p_kargo_takip_no=${tn}`,
  mng: (tn) =>
    `https://www.mngkargo.com.tr/gonderi-takip/?gonderino=${tn}`,
  ptt: (tn) =>
    `https://gonderitakip.ptt.gov.tr/Track/Verify?q=${tn}`,
};

const PROCESSING_POLL_INTERVAL = 10_000;

// ─── Helpers ──────────────────────────────────────────────────────

async function downloadBlob(url: string, filename: string): Promise<void> {
  const token = localStorage.getItem("token");
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("İndirme başarısız");
  const blob = await res.blob();
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(href);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

// ─── Sub-components ───────────────────────────────────────────────

function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-gray-200 ${className}`} />;
}

function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-2xl border bg-white p-4 sm:p-5 ${className}`}>
      {children}
    </div>
  );
}

function CardTitle({
  icon: Icon,
  children,
}: {
  icon: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <Icon className="h-4 w-4 text-gray-500" />
      <h3 className="text-sm font-semibold text-gray-700">{children}</h3>
    </div>
  );
}

// ─── Timeline Stepper ─────────────────────────────────────────────

function TimelineStepper({ status }: { status: string }) {
  const currentIdx = STATUS_ORDER.indexOf(status);

  if (status === "CANCELLED" || status === "REFUNDED") {
    return (
      <Card className="border-red-100 bg-red-50/50">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-100">
            <XCircle className="h-5 w-5 text-red-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-red-800">
              {status === "CANCELLED" ? "İptal Edildi" : "İade Edildi"}
            </p>
            <p className="text-xs text-red-600">
              {status === "CANCELLED"
                ? "Bu sipariş iptal edilmiştir."
                : "Bu sipariş için iade işlemi tamamlanmıştır."}
            </p>
          </div>
        </div>
      </Card>
    );
  }

  if (currentIdx < STATUS_ORDER.indexOf("PAID")) return null;

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-gray-700">
        Sipariş Durumu
      </h3>
      <div className="flex items-center justify-between">
        {TIMELINE_STEPS.map((step, i) => {
          const stepIdx = STATUS_ORDER.indexOf(step.key);
          const done = currentIdx >= stepIdx;
          const active = status === step.key;
          return (
            <div key={step.key} className="flex flex-1 flex-col items-center">
              <div className="relative flex w-full items-center">
                {i > 0 && (
                  <div
                    className={`h-0.5 flex-1 transition-colors ${
                      done ? "bg-purple-500" : "bg-gray-200"
                    }`}
                  />
                )}
                <div
                  className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-all ${
                    done
                      ? active
                        ? "bg-purple-600 text-white ring-4 ring-purple-100"
                        : "bg-purple-500 text-white"
                      : "bg-gray-200 text-gray-400"
                  }`}
                >
                  {done ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <span>{i + 1}</span>
                  )}
                </div>
                {i < TIMELINE_STEPS.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 transition-colors ${
                      currentIdx > stepIdx ? "bg-purple-500" : "bg-gray-200"
                    }`}
                  />
                )}
              </div>
              <span
                className={`mt-2 text-center text-[10px] leading-tight sm:text-xs ${
                  active
                    ? "font-semibold text-purple-700"
                    : done
                      ? "text-purple-600"
                      : "text-gray-400"
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// ─── Production Progress ──────────────────────────────────────────

function ProductionProgress({
  order,
  onLoadPages,
}: {
  order: OrderDetail;
  onLoadPages: () => void;
}) {
  if (order.status !== "PROCESSING") return null;

  const progress =
    order.total_pages > 0
      ? Math.round((order.completed_pages / order.total_pages) * 100)
      : 0;

  return (
    <Card>
      <CardTitle icon={Loader2}>Üretim İlerlemesi</CardTitle>
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>
          {order.completed_pages} / {order.total_pages} sayfa tamamlandı
        </span>
        <span className="font-semibold text-purple-600">{progress}%</span>
      </div>
      <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-violet-500 transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {order.pages && order.pages.length > 0 ? (
        <div className="mt-4 grid grid-cols-8 gap-1.5 sm:grid-cols-12 md:grid-cols-16">
          {order.pages.map((p) => (
            <div
              key={p.page_number}
              title={`Sayfa ${p.page_number}: ${p.status}`}
              className={`flex h-7 w-7 items-center justify-center rounded-lg text-[10px] font-medium transition-colors ${
                p.status === "FULL_GENERATED"
                  ? "bg-green-100 text-green-700"
                  : p.status === "PREVIEW_GENERATED"
                    ? "bg-blue-100 text-blue-700"
                    : p.status === "FAILED"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-400"
              }`}
            >
              {p.page_number}
            </div>
          ))}
        </div>
      ) : (
        <button
          onClick={onLoadPages}
          className="mt-3 text-xs font-medium text-purple-600 hover:text-purple-800"
        >
          Sayfa detaylarını göster
        </button>
      )}
    </Card>
  );
}

// ─── Cargo Tracking ───────────────────────────────────────────────

function CargoTracking({ order }: { order: OrderDetail }) {
  if (!order.tracking_number) return null;

  const carrierKey = (order.carrier || "").toLowerCase();
  const trackingUrl =
    CARRIER_URLS[carrierKey]?.(order.tracking_number) ?? null;

  return (
    <Card>
      <CardTitle icon={Truck}>Kargo Takibi</CardTitle>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-orange-50">
            <Truck className="h-5 w-5 text-orange-500" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900">
              {order.carrier || "Kargo"}
            </p>
            <p className="truncate text-xs text-gray-500">
              {order.tracking_number}
            </p>
          </div>
        </div>
        {trackingUrl && (
          <a href={trackingUrl} target="_blank" rel="noopener noreferrer">
            <Button
              size="sm"
              variant="outline"
              className="shrink-0 rounded-xl text-xs min-h-[44px] px-4"
            >
              Takip Et
              <ExternalLink className="ml-1.5 h-3 w-3" />
            </Button>
          </a>
        )}
      </div>
    </Card>
  );
}

// ─── Invoice Card ─────────────────────────────────────────────────

function InvoiceCard({
  invoice,
  orderId,
  isGuestOrder,
  onRefresh,
}: {
  invoice: InvoiceSummary | null;
  orderId: string;
  isGuestOrder: boolean;
  onRefresh: () => void;
}) {
  const { toast } = useToast();
  const [downloading, setDownloading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  if (!invoice) return null;

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadBlob(
        `${API_BASE_URL}/orders/${orderId}/invoice/download`,
        `fatura_${invoice.invoice_number}.pdf`,
      );
    } catch {
      toast({
        title: "Hata",
        description: "Fatura PDF indirilemedi",
        variant: "destructive",
      });
    } finally {
      setDownloading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      onRefresh();
    } finally {
      setTimeout(() => setRefreshing(false), 1000);
    }
  };

  const renderContent = () => {
    // CANCELLED
    if (invoice.invoice_status === "CANCELLED") {
      return (
        <div className="flex items-center gap-3 rounded-xl bg-red-50 p-3">
          <XCircle className="h-5 w-5 shrink-0 text-red-500" />
          <div>
            <p className="text-sm font-medium text-red-800">
              Fatura iptal edildi
            </p>
            <p className="text-xs text-red-600">
              Detaylar için destek ile iletişime geçin.
            </p>
          </div>
        </div>
      );
    }

    // Guest order — always show email message
    if (isGuestOrder) {
      return (
        <div className="flex items-center gap-3 rounded-xl bg-blue-50 p-3">
          <Mail className="h-5 w-5 shrink-0 text-blue-500" />
          <div>
            <p className="text-sm font-medium text-blue-800">
              Faturanız e-posta ile gönderildi
            </p>
            {invoice.email_sent && (
              <p className="text-xs text-blue-600">
                Fatura numarası: {invoice.invoice_number}
              </p>
            )}
            {!invoice.email_sent &&
              invoice.invoice_status !== "PDF_READY" && (
                <p className="text-xs text-blue-600">
                  Faturanız hazırlanıyor, hazır olduğunda e-posta ile
                  gönderilecektir.
                </p>
              )}
          </div>
        </div>
      );
    }

    // Member — PDF_READY → download button
    if (invoice.pdf_ready) {
      return (
        <div className="space-y-3">
          <div className="flex items-center gap-3 rounded-xl bg-green-50 p-3">
            <FileText className="h-5 w-5 shrink-0 text-green-600" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-green-800">
                Faturanız hazır
              </p>
              <p className="text-xs text-green-600">
                {invoice.invoice_number}
                {invoice.issued_at && ` · ${formatDate(invoice.issued_at)}`}
              </p>
            </div>
          </div>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-green-200 bg-green-50 p-3 text-sm font-medium text-green-700 transition-colors hover:bg-green-100 active:bg-green-200 disabled:opacity-50 min-h-[44px]"
          >
            {downloading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            {downloading ? "İndiriliyor..." : "Fatura PDF İndir"}
          </button>
          {invoice.email_sent && (
            <p className="text-center text-xs text-gray-400">
              Ayrıca e-posta adresinize gönderildi.
            </p>
          )}
        </div>
      );
    }

    // Member — PENDING / ISSUED / FAILED → preparing state
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-3 rounded-xl bg-amber-50 p-3">
          <Clock className="h-5 w-5 shrink-0 text-amber-500" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-amber-800">
              {invoice.invoice_status === "FAILED"
                ? "Fatura oluşturulamadı"
                : "Faturanız hazırlanıyor"}
            </p>
            <p className="text-xs text-amber-600">
              {invoice.invoice_status === "FAILED"
                ? "Tekrar deneniyor, lütfen biraz bekleyin."
                : "Birkaç dakika içinde hazır olacak."}
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-amber-200 bg-white text-amber-600 transition-colors hover:bg-amber-50 active:bg-amber-100"
            aria-label="Fatura durumunu yenile"
          >
            <RefreshCw
              className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      </div>
    );
  };

  return (
    <Card>
      <CardTitle icon={FileText}>Fatura</CardTitle>
      {renderContent()}
    </Card>
  );
}

// ─── Digital Downloads ────────────────────────────────────────────

function DigitalDownloads({ order }: { order: OrderDetail }) {
  const hasContent =
    order.final_pdf_url || order.audio_file_url || order.qr_code_url;
  if (!hasContent) return null;

  const items = [
    {
      url: order.final_pdf_url,
      icon: Download,
      label: "PDF İndir",
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      url: order.audio_file_url,
      icon: Headphones,
      label: "Sesli Kitap",
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      url: order.qr_code_url,
      icon: QrCode,
      label: "QR Kod",
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
  ].filter((item) => item.url);

  return (
    <Card>
      <CardTitle icon={Download}>Dijital İçerikler</CardTitle>
      <div className="grid gap-2 sm:grid-cols-3">
        {items.map((item) => (
          <a
            key={item.label}
            href={item.url!}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex items-center gap-3 rounded-xl border p-3.5 transition-colors hover:${item.bg} active:scale-[0.98] min-h-[44px]`}
          >
            <item.icon className={`h-5 w-5 shrink-0 ${item.color}`} />
            <span className="text-sm font-medium text-gray-700">
              {item.label}
            </span>
          </a>
        ))}
      </div>
    </Card>
  );
}

// ─── Billing Info ─────────────────────────────────────────────────

function BillingInfo({ order }: { order: OrderDetail }) {
  if (!order.billing?.billing_type) return null;

  const b = order.billing;
  const rows: [string, string | undefined | null][] = [
    [
      "Fatura Tipi",
      b.billing_type === "corporate" ? "Kurumsal" : "Bireysel",
    ],
  ];

  if (b.billing_type === "corporate") {
    if (b.billing_company_name) rows.push(["Şirket", b.billing_company_name]);
    if (b.billing_tax_id) rows.push(["Vergi No", b.billing_tax_id]);
    if (b.billing_tax_office)
      rows.push(["Vergi Dairesi", b.billing_tax_office]);
  }
  if (b.billing_full_name) rows.push(["Ad Soyad", b.billing_full_name]);

  const address = b.billing_address;
  if (address) {
    const parts = [address.address, address.district, address.city]
      .filter(Boolean)
      .join(", ");
    if (parts) rows.push(["Fatura Adresi", parts]);
  }

  return (
    <Card>
      <CardTitle icon={FileText}>Fatura Bilgileri</CardTitle>
      <div className="grid gap-2 text-sm">
        {rows.map(
          ([label, value]) =>
            value && (
              <div key={label} className="flex justify-between gap-4">
                <span className="shrink-0 text-gray-500">{label}</span>
                <span className="text-right font-medium text-gray-900">
                  {value}
                </span>
              </div>
            ),
        )}
      </div>
    </Card>
  );
}

// ─── Shipping Address ─────────────────────────────────────────────

function ShippingAddress({ order }: { order: OrderDetail }) {
  if (!order.shipping_address) return null;
  const a = order.shipping_address;

  return (
    <Card>
      <CardTitle icon={Truck}>Teslimat Adresi</CardTitle>
      <p className="text-sm leading-relaxed text-gray-600">
        {a.full_name}
        <br />
        {a.address_line1}
        {a.address_line2 && (
          <>
            <br />
            {a.address_line2}
          </>
        )}
        <br />
        {a.district && `${a.district}, `}
        {a.city}
        {a.postal_code && ` ${a.postal_code}`}
      </p>
    </Card>
  );
}

// ─── KVKK Card ────────────────────────────────────────────────────

function KvkkCard({
  onDelete,
  deleting,
}: {
  onDelete: () => void;
  deleting: boolean;
}) {
  return (
    <Card>
      <CardTitle icon={Shield}>Veri Güvenliği</CardTitle>
      <p className="mb-3 text-xs leading-relaxed text-gray-500">
        Fotoğraf verileri KVKK kapsamında teslimattan 30 gün sonra otomatik
        silinir. Dilediğiniz zaman hemen silme talebinde bulunabilirsiniz.
      </p>
      <Button
        variant="outline"
        size="sm"
        onClick={onDelete}
        disabled={deleting}
        className="rounded-xl text-xs text-red-600 border-red-200 hover:bg-red-50 min-h-[44px] px-4"
      >
        <Trash2 className="mr-1.5 h-3.5 w-3.5" />
        {deleting ? "Siliniyor..." : "Fotoğrafımı Şimdi Sil"}
      </Button>
    </Card>
  );
}

// ─── Support Card ─────────────────────────────────────────────────

function SupportCard({ orderId }: { orderId: string }) {
  const shortId = orderId.slice(0, 8);
  return (
    <Card>
      <CardTitle icon={Headphones}>Yardım & Destek</CardTitle>
      <div className="grid grid-cols-2 gap-2">
        <a
          href={`https://wa.me/905XXXXXXXXX?text=Sipariş No: ${shortId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2.5 rounded-xl border p-3.5 transition-colors hover:bg-gray-50 active:bg-gray-100 min-h-[44px]"
        >
          <MessageCircle className="h-4 w-4 text-green-600" />
          <span className="text-xs font-medium text-gray-700">WhatsApp</span>
        </a>
        <a
          href={`mailto:destek@benimmasalim.com?subject=Sipariş ${shortId} Hakkında`}
          className="flex items-center gap-2.5 rounded-xl border p-3.5 transition-colors hover:bg-gray-50 active:bg-gray-100 min-h-[44px]"
        >
          <Mail className="h-4 w-4 text-blue-600" />
          <span className="text-xs font-medium text-gray-700">E-posta</span>
        </a>
      </div>
    </Card>
  );
}

// ─── Timeline Events (Audit Log) ─────────────────────────────────

function TimelineEvents({
  order,
  loaded,
  onLoad,
}: {
  order: OrderDetail;
  loaded: boolean;
  onLoad: () => void;
}) {
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <CardTitle icon={Clock}>Geçmiş</CardTitle>
        {!loaded && (
          <button
            onClick={onLoad}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-purple-600 transition-colors hover:bg-purple-50 active:bg-purple-100 min-h-[36px]"
          >
            Yükle
          </button>
        )}
      </div>
      {order.timeline_events && order.timeline_events.length > 0 ? (
        <div className="space-y-3">
          {order.timeline_events.map((e, i) => (
            <div key={i} className="flex items-start gap-3">
              <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-purple-400" />
              <div>
                <p className="text-xs font-medium text-gray-700">{e.status}</p>
                <p className="text-[10px] text-gray-400">
                  {new Date(e.timestamp).toLocaleString("tr-TR")}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : loaded ? (
        <p className="text-xs text-gray-400">Henüz geçmiş kaydı yok.</p>
      ) : (
        <p className="text-xs text-gray-400">
          Geçmiş bilgilerini görmek için &quot;Yükle&quot; butonuna tıklayın.
        </p>
      )}
    </Card>
  );
}

// ─── Main Page ────────────────────────────────────────────────────

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [deletingPhoto, setDeletingPhoto] = useState(false);
  const [pagesLoaded, setPagesLoaded] = useState(false);
  const [timelineLoaded, setTimelineLoaded] = useState(false);
  const [isGuest, setIsGuest] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Initial load
  useEffect(() => {
    if (!id) return;
    Promise.all([
      getOrderDetail(id),
      getUserProfile().catch(() => null),
    ])
      .then(([orderData, profile]) => {
        setOrder(orderData);
        if (profile) setIsGuest(profile.is_guest === true);
      })
      .catch(() =>
        toast({
          title: "Hata",
          description: "Sipariş yüklenemedi",
          variant: "destructive",
        }),
      )
      .finally(() => setLoading(false));
  }, [id, toast]);

  // Auto-poll during PROCESSING
  useEffect(() => {
    if (order?.status !== "PROCESSING" || !id) return;

    pollRef.current = setInterval(async () => {
      try {
        const updated = await getOrderDetail(id, "pages");
        setOrder((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            status: updated.status,
            status_description: updated.status_description,
            status_hint: updated.status_hint,
            completed_pages: updated.completed_pages,
            total_pages: updated.total_pages,
            pages: updated.pages ?? prev.pages,
            invoice: updated.invoice ?? prev.invoice,
          };
        });
        setPagesLoaded(true);
        if (updated.status !== "PROCESSING" && pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch {
        /* silent — retry next interval */
      }
    }, PROCESSING_POLL_INTERVAL);

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [order?.status, id]);

  const loadPages = useCallback(async () => {
    if (!id || pagesLoaded) return;
    try {
      const detail = await getOrderDetail(id, "pages");
      setOrder((prev) =>
        prev ? { ...prev, pages: detail.pages } : prev,
      );
      setPagesLoaded(true);
    } catch {
      /* silent */
    }
  }, [id, pagesLoaded]);

  const loadTimeline = useCallback(async () => {
    if (!id || timelineLoaded) return;
    try {
      const detail = await getOrderDetail(id, "timeline");
      setOrder((prev) =>
        prev
          ? { ...prev, timeline_events: detail.timeline_events }
          : prev,
      );
      setTimelineLoaded(true);
    } catch {
      /* silent */
    }
  }, [id, timelineLoaded]);

  const refreshOrder = useCallback(async () => {
    if (!id) return;
    try {
      const updated = await getOrderDetail(id);
      setOrder(updated);
    } catch {
      /* silent */
    }
  }, [id]);

  const handleDeletePhoto = async () => {
    if (
      !confirm(
        "Fotoğraf ve yüz verileri kalıcı olarak silinecek. Devam etmek istiyor musunuz?",
      )
    )
      return;
    setDeletingPhoto(true);
    try {
      await deletePhotoNow(order!.id);
      toast({
        title: "Silindi",
        description: "Fotoğraf ve yüz verileri silindi.",
      });
      const updated = await getOrderDetail(order!.id);
      setOrder(updated);
    } catch (e) {
      toast({
        title: "Hata",
        description: e instanceof Error ? e.message : "Silinemedi",
        variant: "destructive",
      });
    } finally {
      setDeletingPhoto(false);
    }
  };

  // ─── Loading skeleton ────────────────────────────────────────

  if (loading) {
    return (
      <div className="space-y-4 py-6">
        <Skeleton className="h-4 w-16" />
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <Skeleton className="h-6 w-40" />
            <Skeleton className="h-4 w-56" />
          </div>
          <Skeleton className="h-6 w-20" />
        </div>
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-20 rounded-2xl" />
        <Skeleton className="h-16 rounded-2xl" />
        <Skeleton className="h-16 rounded-2xl" />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="flex flex-col items-center py-20">
        <Package className="h-12 w-12 text-gray-300" />
        <p className="mt-4 text-gray-600">Sipariş bulunamadı</p>
        <Link href="/account">
          <Button variant="outline" className="mt-4 rounded-xl">
            Siparişlerime Dön
          </Button>
        </Link>
      </div>
    );
  }

  const isGuestOrder = order.is_guest_order || isGuest;

  return (
    <div className="space-y-4 pb-24 sm:pb-6">
      {/* Back button */}
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 active:bg-gray-200 min-h-[36px]"
        aria-label="Geri dön"
      >
        <ArrowLeft className="h-4 w-4" />
        Geri
      </button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">
            {order.child_name}
          </h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Sipariş: {order.id.slice(0, 8)}... &middot;{" "}
            {formatDate(order.created_at)}
          </p>
        </div>
        {order.payment_amount != null && order.payment_amount > 0 && (
          <span className="shrink-0 text-lg font-bold text-gray-900">
            {order.payment_amount.toFixed(2)} TL
          </span>
        )}
      </div>

      {/* Status banner */}
      {order.status !== "CANCELLED" && order.status !== "REFUNDED" && (
        <div className="rounded-2xl border-2 border-purple-100 bg-gradient-to-r from-purple-50 to-violet-50 p-4">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-purple-100">
              <AlertCircle className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-purple-900">
                Şu An Ne Oluyor?
              </p>
              <p className="text-sm text-purple-700">
                {order.status_description}
              </p>
              {order.status_hint && (
                <p className="mt-0.5 text-xs text-purple-600/70">
                  {order.status_hint}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Timeline stepper */}
      <TimelineStepper status={order.status} />

      {/* Production progress (auto-polls) */}
      <ProductionProgress order={order} onLoadPages={loadPages} />

      {/* Cargo tracking */}
      <CargoTracking order={order} />

      {/* Digital downloads */}
      <DigitalDownloads order={order} />

      {/* Invoice card */}
      <InvoiceCard
        invoice={order.invoice}
        orderId={order.id}
        isGuestOrder={isGuestOrder}
        onRefresh={refreshOrder}
      />

      {/* Billing info */}
      <BillingInfo order={order} />

      {/* Shipping address */}
      <ShippingAddress order={order} />

      {/* KVKK */}
      <KvkkCard
        onDelete={handleDeletePhoto}
        deleting={deletingPhoto}
      />

      {/* Support */}
      <SupportCard orderId={order.id} />

      {/* Timeline events */}
      <TimelineEvents
        order={order}
        loaded={timelineLoaded}
        onLoad={loadTimeline}
      />

      {/* Delivered date */}
      {order.delivered_at && (
        <p className="text-center text-xs text-gray-400">
          Teslim tarihi: {formatDate(order.delivered_at)}
        </p>
      )}
    </div>
  );
}
