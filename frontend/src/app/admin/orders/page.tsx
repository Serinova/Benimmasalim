"use client";

import { useEffect, useState } from "react";
import { useAdminAuth } from "@/hooks/use-admin-auth";
import { useOrdersList } from "./_hooks/useOrdersList";
import { useOrderDetail } from "./_hooks/useOrderDetail";
import { useOrderActions } from "./_hooks/useOrderActions";
import { StatsCards } from "./_components/StatsCards";
import { OrdersToolbar } from "./_components/OrdersToolbar";
import { OrdersTable } from "./_components/OrdersTable";
import { OrderDetailSheet } from "./_components/OrderDetailSheet";

export default function AdminOrdersPage() {
  const [compact, setCompact] = useState(false);

  // Auto-compact on small screens
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 768px)");
    setCompact(mq.matches);
    const handler = (e: MediaQueryListEvent) => setCompact(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  useAdminAuth();

  const list = useOrdersList();
  const detailHook = useOrderDetail();
  const actions = useOrderActions({
    detail: detailHook.detail,
    refreshDetail: detailHook.refreshDetail,
    refreshList: list.refreshList,
    updateDetailLocal: detailHook.updateDetailLocal,
  });

  return (
    <div>
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-800">Sipariş Yönetimi</h1>
        <div className="text-xs text-slate-400">
          {list.total} sipariş
        </div>
      </div>

      <div className="space-y-4">
        {/* Stats */}
        <StatsCards
          stats={list.stats}
          invoiceDashboard={list.invoiceDashboard}
          showInvoiceReports={list.showInvoiceReports}
          onToggleInvoiceReports={() => {
            list.setShowInvoiceReports(!list.showInvoiceReports);
            if (!list.showInvoiceReports) list.loadInvoiceDashboard();
          }}
          invoiceReportType={list.invoiceReportType}
          invoiceReportData={list.invoiceReportData}
          invoiceReportLoading={list.invoiceReportLoading}
          onLoadInvoiceReport={list.loadInvoiceReport}
          onCloseReport={() => { list.setInvoiceReportData(null); list.setInvoiceReportType(""); }}
        />

        {/* Toolbar */}
        <OrdersToolbar
          statusFilter={list.statusFilter}
          onStatusChange={list.setStatusFilter}
          searchQuery={list.searchQuery}
          onSearchChange={list.setSearchQuery}
          dateFrom={list.dateFrom}
          onDateFromChange={list.setDateFrom}
          dateTo={list.dateTo}
          onDateToChange={list.setDateTo}
          items={list.items}
          compact={compact}
          onCompactToggle={() => setCompact((c) => !c)}
        />

        {/* Table */}
        <OrdersTable
          items={list.items}
          total={list.total}
          currentPage={list.currentPage}
          loading={list.loading}
          error={list.error}
          selectedId={detailHook.selectedId}
          onSelectOrder={detailHook.selectOrder}
          onPageChange={list.goToPage}
          compact={compact}
        />
      </div>

      {/* Detail Sheet */}
      <OrderDetailSheet
        open={detailHook.selectedId !== null}
        onOpenChange={(open) => { if (!open) detailHook.closeDetail(); }}
        detail={detailHook.detail}
        loading={detailHook.loading}
        backCoverConfig={detailHook.backCoverConfig}
        onUpdateStatus={actions.updateStatus}
        onGenerateBook={actions.handleGenerateBook}
        onDownloadPdf={actions.handleDownloadPdf}
        onColoringBook={actions.handleColoringBook}
        onInvoiceAction={actions.handleInvoiceAction}
        onDownloadInvoicePdf={actions.handleDownloadInvoicePdf}
        onCreateInvoice={actions.handleCreateInvoice}
        onGenerateRemaining={actions.handleGenerateRemaining}
        onRecompose={actions.handleRecompose}
        onDownloadSingleImage={actions.downloadSingleImage}
        onDownloadAllImages={actions.downloadAllImages}
        pdfDownloading={actions.pdfDownloading}
        zipDownloading={actions.zipDownloading}
        bookGenerating={actions.bookGenerating}
        coloringGenerating={actions.coloringGenerating}
      />
    </div>
  );
}
