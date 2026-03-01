"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getUserOrdersPaginated,
  getUserTrials,
  getUserPaidTrials,
  type PaginatedOrders,
  type UserTrial,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import GuestConvertBanner from "@/components/GuestConvertBanner";
import { AccountOrderDetailSheet } from "./_components/AccountOrderDetailSheet";
import { AccountTrialDetailSheet } from "./_components/AccountTrialDetailSheet";
import {
  Package,
  Search,
  Truck,
  Headphones,
  Loader2,
  ChevronRight,
} from "lucide-react";

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  DRAFT: { label: "Taslak", color: "text-gray-600", bg: "bg-gray-100" },
  TEXT_APPROVED: { label: "Metin Onaylandı", color: "text-blue-600", bg: "bg-blue-50" },
  COVER_APPROVED: { label: "Kapak Onaylandı", color: "text-blue-600", bg: "bg-blue-50" },
  PAYMENT_PENDING: { label: "Ödeme Bekliyor", color: "text-amber-600", bg: "bg-amber-50" },
  PAID: { label: "Ödendi", color: "text-green-600", bg: "bg-green-50" },
  PROCESSING: { label: "Üretiliyor", color: "text-purple-600", bg: "bg-purple-50" },
  COMPLETING: { label: "Kitap Hazırlanıyor", color: "text-purple-600", bg: "bg-purple-50" },
  COMPLETED: { label: "Tamamlandı", color: "text-emerald-600", bg: "bg-emerald-50" },
  READY_FOR_PRINT: { label: "Baskıya Hazır", color: "text-indigo-600", bg: "bg-indigo-50" },
  SHIPPED: { label: "Kargoda", color: "text-orange-600", bg: "bg-orange-50" },
  DELIVERED: { label: "Teslim Edildi", color: "text-emerald-600", bg: "bg-emerald-50" },
  CANCELLED: { label: "İptal", color: "text-red-600", bg: "bg-red-50" },
  REFUNDED: { label: "İade", color: "text-red-600", bg: "bg-red-50" },
};

const FILTERS = [
  { key: "", label: "Tümü" },
  { key: "active", label: "Devam Ediyor" },
  { key: "delivered", label: "Teslim Edilen" },
  { key: "cancelled", label: "İptal / İade" },
];

function matchesSearch(
  q: string,
  childName: string,
  storyTitle?: string | null,
  orderId?: string,
): boolean {
  const s = (q || "").trim().toLowerCase();
  if (!s) return true;
  const child = (childName || "").toLowerCase();
  const story = (storyTitle || "").toLowerCase();
  const id = (orderId || "").toLowerCase();
  return child.includes(s) || story.includes(s) || id.includes(s);
}

export default function AccountPage() {
  const router = useRouter();
  const [data, setData] = useState<PaginatedOrders | null>(null);
  const [trials, setTrials] = useState<UserTrial[]>([]);
  const [paidTrials, setPaidTrials] = useState<UserTrial[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [isGuest, setIsGuest] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [selectedTrial, setSelectedTrial] = useState<UserTrial | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    debounceRef.current = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 400);
    return () => clearTimeout(debounceRef.current);
  }, [search]);

  const fetchOrders = useCallback(async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    try {
      const res = await getUserOrdersPaginated({
        status_filter: filter || undefined,
        search: debouncedSearch || undefined,
        page,
        per_page: 10,
      });
      if (!controller.signal.aborted) setData(res);
    } catch {
      if (!abortRef.current?.signal.aborted) setData(null);
    } finally {
      if (!abortRef.current?.signal.aborted) setLoading(false);
    }
  }, [filter, debouncedSearch, page]);

  useEffect(() => {
    fetchOrders();
    getUserTrials().then(setTrials).catch(() => {});
    getUserPaidTrials().then(setPaidTrials).catch(() => {});
    try {
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      setIsGuest(user.is_guest === true);
    } catch {
      /* ignore */
    }
  }, [fetchOrders]);

  const orders = data?.items ?? [];
  const totalPages = data?.total_pages ?? 0;
  const totalCount = data?.total ?? 0;

  const isOngoingTrial = (t: UserTrial) =>
    ["COMPLETING", "COMPLETED", "PAYMENT_PENDING"].includes(t.status);
  const visibleTrials =
    filter === "" || filter === "active" ? trials : [];
  const visiblePaidTrials =
    filter === ""
      ? paidTrials
      : filter === "active"
        ? paidTrials.filter(isOngoingTrial)
        : filter === "delivered" || filter === "cancelled"
          ? []
          : paidTrials;
  const visibleOrders = orders;
  const searchMatches = (child: string, story?: string | null, id?: string) =>
    matchesSearch(debouncedSearch, child, story, id);
  const filteredTrials = visibleTrials.filter((t) =>
    searchMatches(t.child_name, t.story_title),
  );
  const filteredPaidTrials = visiblePaidTrials.filter((t) =>
    searchMatches(t.child_name, t.story_title),
  );
  const filteredOrders = visibleOrders;
  const combinedCount =
    filteredTrials.length + filteredPaidTrials.length + filteredOrders.length;

  const handleSelectOrder = (id: string) => {
    setSelectedTrial(null);
    setSelectedOrderId(id);
  };

  const handleSelectTrial = (trial: UserTrial) => {
    setSelectedOrderId(null);
    setSelectedTrial(trial);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header - admin orders style */}
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push("/")}
              className="rounded-lg"
            >
              ← Geri
            </Button>
            <h1 className="text-xl font-bold text-slate-800">Siparişlerim</h1>
          </div>
          <div className="text-sm text-slate-500">
            {combinedCount} sipariş
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] space-y-4 px-4 py-4 sm:px-6">
        {isGuest && (
          <GuestConvertBanner onConverted={() => { setIsGuest(false); fetchOrders(); }} />
        )}

        {/* Toolbar - filters + search */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-2 overflow-x-auto">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => { setFilter(f.key); setPage(1); }}
                className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
                  filter === f.key
                    ? "bg-purple-600 text-white"
                    : "border bg-white text-gray-600 hover:bg-gray-50"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
          <div className="relative flex-1 sm:max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Çocuk adı veya sipariş no ile ara..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 rounded-lg pl-9 text-sm"
            />
          </div>
        </div>

        {/* Table - admin orders style */}
        <div className="overflow-hidden rounded-lg border bg-white">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                <span className="text-sm text-slate-500">Siparişler yükleniyor...</span>
              </div>
            </div>
          ) : filteredTrials.length === 0 && filteredPaidTrials.length === 0 && filteredOrders.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Package className="h-12 w-12 text-slate-300" />
              <h3 className="mt-4 text-base font-semibold text-slate-700">Henüz sipariş yok</h3>
              <p className="mt-1 text-sm text-slate-500">İlk masalınızı oluşturmaya başlayın!</p>
              <Link href="/create-v2">
                <Button className="mt-4 rounded-xl bg-purple-600 hover:bg-purple-700">
                  Masal Oluştur
                </Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="whitespace-nowrap px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Sipariş / Hikaye
                    </th>
                    <th className="whitespace-nowrap px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Tarih
                    </th>
                    <th className="whitespace-nowrap px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Durum
                    </th>
                    <th className="whitespace-nowrap px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Tutar
                    </th>
                    <th className="w-10 px-2" />
                  </tr>
                </thead>
                <tbody>
                  {/* Devam eden önizlemeler */}
                  {filteredTrials.map((t) => {
                    const cfg = STATUS_CONFIG[t.status] || STATUS_CONFIG.PROCESSING;
                    return (
                      <tr
                        key={`trial-${t.id}`}
                        className="cursor-pointer border-b border-slate-100 transition-colors hover:bg-slate-50"
                        onClick={() => handleSelectTrial(t)}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex h-9 w-7 shrink-0 items-center justify-center rounded bg-purple-100 text-xs">
                              📖
                            </div>
                            <div className="min-w-0">
                              <div className="truncate text-sm font-medium text-slate-800">
                                {t.child_name}
                              </div>
                              <div className="truncate text-xs text-slate-500">
                                {t.story_title} — Devam ediyor
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-600">
                          {new Date(t.created_at).toLocaleDateString("tr-TR")}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cfg.color} ${cfg.bg}`}>
                            {cfg.label}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-slate-700">
                          {t.product_price != null ? `${t.product_price.toFixed(2)} TL` : "—"}
                        </td>
                        <td className="px-2 py-3">
                          <ChevronRight className="h-4 w-4 text-slate-400" />
                        </td>
                      </tr>
                    );
                  })}
                  {/* Ödenen önizlemeler / Hikaye kitapları */}
                  {filteredPaidTrials.map((t) => {
                    const cfg = STATUS_CONFIG[t.status] || STATUS_CONFIG.PROCESSING;
                    return (
                      <tr
                        key={`trial-${t.id}`}
                        className="cursor-pointer border-b border-slate-100 transition-colors hover:bg-slate-50"
                        onClick={() => handleSelectTrial(t)}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex h-9 w-7 shrink-0 items-center justify-center rounded bg-purple-100 text-xs">
                              📖
                            </div>
                            <div className="min-w-0">
                              <div className="truncate text-sm font-medium text-slate-800">
                                {t.child_name}
                              </div>
                              <div className="truncate text-xs text-slate-500">
                                {t.story_title}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-600">
                          {new Date(t.created_at).toLocaleDateString("tr-TR")}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cfg.color} ${cfg.bg}`}>
                            {cfg.label}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-slate-700">
                          {t.product_price != null ? `${t.product_price.toFixed(2)} TL` : "—"}
                        </td>
                        <td className="px-2 py-3">
                          <ChevronRight className="h-4 w-4 text-slate-400" />
                        </td>
                      </tr>
                    );
                  })}
                  {/* Orders from Order table */}
                  {orders.map((order) => {
                    const cfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.DRAFT;
                    const progress = order.total_pages > 0
                      ? Math.round((order.completed_pages / order.total_pages) * 100)
                      : 0;
                    return (
                      <tr
                        key={order.id}
                        className={`cursor-pointer border-b border-slate-100 transition-colors hover:bg-slate-50 ${
                          selectedOrderId === order.id ? "bg-purple-50" : ""
                        }`}
                        onClick={() => handleSelectOrder(order.id)}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex h-9 w-7 shrink-0 items-center justify-center rounded bg-slate-100 text-[10px] font-mono">
                              {order.id.slice(0, 6)}
                            </div>
                            <div className="min-w-0">
                              <div className="truncate text-sm font-medium text-slate-800">
                                {order.child_name}
                              </div>
                              <div className="truncate text-xs text-slate-500">
                                {order.tracking_number ? (
                                  <span className="flex items-center gap-1">
                                    <Truck className="h-3 w-3" />
                                    {order.tracking_number}
                                  </span>
                                ) : (
                                  order.status === "PROCESSING"
                                    ? `Üretim: ${order.completed_pages}/${order.total_pages} sayfa (${progress}%)`
                                    : order.created_at
                                )}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-600">
                          {new Date(order.created_at).toLocaleDateString("tr-TR")}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cfg.color} ${cfg.bg}`}>
                            {cfg.label}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-slate-700">
                          {order.payment_amount != null ? `${order.payment_amount.toFixed(2)} TL` : "—"}
                        </td>
                        <td className="px-2 py-3">
                          <div className="flex items-center gap-1">
                            {order.has_audio_book && (
                              <Headphones className="h-4 w-4 text-blue-500" />
                            )}
                            <ChevronRight className="h-4 w-4 text-slate-400" />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {!loading && orders.length > 0 && totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 border-t bg-slate-50 px-4 py-3">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-lg text-xs"
              >
                Önceki
              </Button>
              <span className="text-xs text-slate-500">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-lg text-xs"
              >
                Sonraki
              </Button>
            </div>
          )}
        </div>
      </main>

      {/* Detail sheets */}
      <AccountOrderDetailSheet
        orderId={selectedOrderId}
        open={selectedOrderId !== null}
        onOpenChange={(open) => { if (!open) setSelectedOrderId(null); }}
      />
      <AccountTrialDetailSheet
        trial={selectedTrial}
        open={selectedTrial !== null}
        onOpenChange={(open) => { if (!open) setSelectedTrial(null); }}
      />
    </div>
  );
}
