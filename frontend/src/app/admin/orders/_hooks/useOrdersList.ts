"use client";

import { useState, useEffect, useCallback } from "react";
import type { OrderListItem, OrderStats, InvoiceDashboard } from "../_lib/types";
import {
  fetchOrdersList,
  fetchOrderStats,
  fetchInvoiceDashboard as fetchInvoiceDashboardApi,
  fetchInvoiceReport as fetchInvoiceReportApi,
} from "../_lib/adminOrdersApi";
import { PAGE_SIZE } from "../_lib/constants";

export function useOrdersList() {
  const [items, setItems] = useState<OrderListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Stats
  const [stats, setStats] = useState<OrderStats | null>(null);

  // Invoice dashboard
  const [invoiceDashboard, setInvoiceDashboard] = useState<InvoiceDashboard | null>(null);
  const [showInvoiceReports, setShowInvoiceReports] = useState(false);
  const [invoiceReportData, setInvoiceReportData] = useState<Record<string, unknown>[] | null>(null);
  const [invoiceReportType, setInvoiceReportType] = useState("");
  const [invoiceReportLoading, setInvoiceReportLoading] = useState(false);

  const loadList = useCallback(async (page: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchOrdersList({
        status: statusFilter || undefined,
        page,
        pageSize: PAGE_SIZE,
        search: searchQuery || undefined,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
      });
      setItems(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Siparişler yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, searchQuery, dateFrom, dateTo]);

  const loadStats = useCallback(async () => {
    try {
      const s = await fetchOrderStats();
      setStats(s);
    } catch { /* silent */ }
  }, []);

  const loadInvoiceDashboard = useCallback(async () => {
    const d = await fetchInvoiceDashboardApi();
    setInvoiceDashboard(d);
  }, []);

  const loadInvoiceReport = useCallback(async (type: string) => {
    setInvoiceReportLoading(true);
    setInvoiceReportType(type);
    setInvoiceReportData(null);
    try {
      const data = await fetchInvoiceReportApi(type);
      setInvoiceReportData(data);
    } catch {
      setInvoiceReportData(null);
    } finally {
      setInvoiceReportLoading(false);
    }
  }, []);

  // Reload on filter change
  useEffect(() => {
    setCurrentPage(0);
    loadList(0);
    loadStats();
    loadInvoiceDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, searchQuery, dateFrom, dateTo]);

  const goToPage = useCallback((page: number) => {
    setCurrentPage(page);
    loadList(page);
  }, [loadList]);

  const refreshList = useCallback(() => {
    loadList(currentPage);
    loadStats();
  }, [loadList, loadStats, currentPage]);

  return {
    items,
    total,
    currentPage,
    loading,
    error,
    stats,
    // Filters
    statusFilter,
    setStatusFilter,
    searchQuery,
    setSearchQuery,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    // Pagination
    goToPage,
    pageSize: PAGE_SIZE,
    // Refresh
    refreshList,
    // Invoice dashboard
    invoiceDashboard,
    showInvoiceReports,
    setShowInvoiceReports,
    invoiceReportData,
    invoiceReportType,
    invoiceReportLoading,
    loadInvoiceReport,
    loadInvoiceDashboard,
    setInvoiceReportData,
    setInvoiceReportType,
  };
}
