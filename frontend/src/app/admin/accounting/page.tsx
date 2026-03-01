"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Calendar, RefreshCw, TrendingUp, Package, Ticket, List, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

import SummaryCards from "./_components/SummaryCards";
import RevenueChart from "./_components/RevenueChart";
import ProductBreakdown from "./_components/ProductBreakdown";
import PromoTable from "./_components/PromoTable";
import TransactionLedger from "./_components/TransactionLedger";

import {
  fetchSummary,
  fetchRevenueOverTime,
  fetchByProduct,
  fetchPromoAnalysis,
  fetchTransactions,
  downloadTransactionsCsv,
  type AccountingSummary,
  type RevenuePoint,
  type ProductRevenue,
  type PromoStat,
  type TransactionsResponse,
} from "./_lib/accountingApi";

// ── Date helpers ──────────────────────────────────────────────────────────

function today() {
  return new Date().toISOString().slice(0, 10);
}

function firstDayOfMonth() {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}

function firstDayOfYear() {
  return `${new Date().getFullYear()}-01-01`;
}

type Preset = "this_month" | "this_year" | "all_time" | "custom";

const PRESETS: { label: string; value: Preset }[] = [
  { label: "Bu Ay", value: "this_month" },
  { label: "Bu Yıl", value: "this_year" },
  { label: "Tüm Zamanlar", value: "all_time" },
  { label: "Özel Aralık", value: "custom" },
];

function presetDates(preset: Preset): { from: string | undefined; to: string | undefined } {
  const td = today();
  if (preset === "this_month") return { from: firstDayOfMonth(), to: td };
  if (preset === "this_year") return { from: firstDayOfYear(), to: td };
  if (preset === "all_time") return { from: undefined, to: undefined };
  return { from: undefined, to: undefined }; // custom — let user pick
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function AccountingPage() {
  const [preset, setPreset] = useState<Preset>("this_month");
  const [customFrom, setCustomFrom] = useState<string>(firstDayOfMonth());
  const [customTo, setCustomTo] = useState<string>(today());
  const [period, setPeriod] = useState<"daily" | "weekly" | "monthly">("daily");
  const [txSearch, setTxSearch] = useState("");
  const [txPage, setTxPage] = useState(1);
  const [refreshKey, setRefreshKey] = useState(0);
  const [csvLoading, setCsvLoading] = useState(false);

  // Data state
  const [summary, setSummary] = useState<AccountingSummary | null>(null);
  const [revenue, setRevenue] = useState<RevenuePoint[]>([]);
  const [byProduct, setByProduct] = useState<ProductRevenue[]>([]);
  const [promos, setPromos] = useState<PromoStat[]>([]);
  const [transactions, setTransactions] = useState<TransactionsResponse | null>(null);

  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingRevenue, setLoadingRevenue] = useState(true);
  const [loadingProduct, setLoadingProduct] = useState(true);
  const [loadingPromo, setLoadingPromo] = useState(true);
  const [loadingTx, setLoadingTx] = useState(true);

  const { from, to } = preset === "custom"
    ? { from: customFrom, to: customTo }
    : presetDates(preset);

  const fetchAll = useCallback(async () => {
    setLoadingSummary(true);
    setLoadingRevenue(true);
    setLoadingProduct(true);
    setLoadingPromo(true);

    try {
      const [s, r, p, pr] = await Promise.all([
        fetchSummary(from, to),
        fetchRevenueOverTime(period, from, to),
        fetchByProduct(from, to),
        fetchPromoAnalysis(from, to),
      ]);
      setSummary(s);
      setRevenue(r);
      setByProduct(p);
      setPromos(pr);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSummary(false);
      setLoadingRevenue(false);
      setLoadingProduct(false);
      setLoadingPromo(false);
    }
  }, [from, to, period, refreshKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchTxns = useCallback(async () => {
    setLoadingTx(true);
    try {
      const res = await fetchTransactions({
        from_date: from,
        to_date: to,
        page: txPage,
        limit: 50,
        search: txSearch || undefined,
      });
      setTransactions(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingTx(false);
    }
  }, [from, to, txPage, txSearch, refreshKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    setTxPage(1);
  }, [from, to, txSearch]);

  useEffect(() => {
    fetchTxns();
  }, [fetchTxns]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* ── Header ── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Muhasebe & Gelir Analizi</h1>
          <p className="mt-1 text-sm text-slate-500">
            Tüm satış, indirim, KDV ve iade hareketlerini takip edin
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={async () => {
              setCsvLoading(true);
              try { await downloadTransactionsCsv(from, to); } catch { /* ignore */ }
              finally { setCsvLoading(false); }
            }}
            disabled={csvLoading}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {csvLoading ? "İndiriliyor..." : "CSV İndir"}
          </button>
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
          >
            <RefreshCw className="h-4 w-4" />
            Yenile
          </button>
        </div>
      </div>

      {/* ── Date Range Toolbar ── */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
        <Calendar className="h-4 w-4 text-slate-400" />
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPreset(p.value)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                preset === p.value
                  ? "bg-indigo-600 text-white"
                  : "border border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {preset === "custom" && (
          <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
            <input
              type="date"
              value={customFrom}
              onChange={(e) => setCustomFrom(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <span className="text-slate-400">—</span>
            <input
              type="date"
              value={customTo}
              onChange={(e) => setCustomTo(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}
      </div>

      {/* ── Summary Cards ── */}
      <SummaryCards data={summary} loading={loadingSummary} />

      {/* ── Revenue Chart ── */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="flex flex-col gap-3 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-500" />
            <div>
              <CardTitle className="text-base font-semibold">Gelir Grafiği</CardTitle>
              <CardDescription className="text-xs">Net gelir zaman serisinde</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 p-0.5">
            {(["daily", "weekly", "monthly"] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  period === p ? "bg-white text-indigo-700 shadow-sm" : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {p === "daily" ? "Günlük" : p === "weekly" ? "Haftalık" : "Aylık"}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          <RevenueChart data={revenue} period={period} loading={loadingRevenue} />
        </CardContent>
      </Card>

      {/* ── Product + Promo row ── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Package className="h-5 w-5 text-violet-500" />
              <div>
                <CardTitle className="text-base font-semibold">Ürün Bazlı Gelir</CardTitle>
                <CardDescription className="text-xs">En çok gelir getiren ürünler</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ProductBreakdown data={byProduct} loading={loadingProduct} />
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Ticket className="h-5 w-5 text-amber-500" />
              <div>
                <CardTitle className="text-base font-semibold">Kupon Kodu Analizi</CardTitle>
                <CardDescription className="text-xs">Kullanım ve indirim etkisi</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <PromoTable data={promos} loading={loadingPromo} />
          </CardContent>
        </Card>
      </div>

      {/* ── Transaction Ledger ── */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-2">
            <List className="h-5 w-5 text-slate-500" />
            <div>
              <CardTitle className="text-base font-semibold">İşlem Defteri</CardTitle>
              <CardDescription className="text-xs">
                Tüm ödemeler — brüt, net, KDV ve indirim detaylı
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <TransactionLedger
            data={transactions}
            loading={loadingTx}
            search={txSearch}
            onSearchChange={(v) => setTxSearch(v)}
            onPageChange={(p) => setTxPage(p)}
          />
        </CardContent>
      </Card>
    </motion.div>
  );
}
