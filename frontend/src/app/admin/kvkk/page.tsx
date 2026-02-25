"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { API_BASE_URL } from "@/lib/api";

// Types
interface KVKKStats {
  total_users: number;
  total_orders_with_photos: number;
  pending_deletions: number;
  deleted_last_30_days: number;
  next_scheduled_deletion: string | null;
  kvkk_retention_days: number;
}

interface DeletionQueueItem {
  order_id: string;
  child_name: string;
  delivered_at: string;
  scheduled_deletion: string;
  days_remaining: number;
  has_photo: boolean;
  has_cloned_voice: boolean;
}

interface AuditLogItem {
  id: number;
  action: string;
  order_id: string | null;
  user_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

interface UserListItem {
  id: string;
  email: string | null;
  full_name: string | null;
  orders_count: number;
  photos_count: number;
  created_at: string;
  is_active: boolean;
}

export default function KVKKPage() {
  const [stats, setStats] = useState<KVKKStats | null>(null);
  const [deletionQueue, setDeletionQueue] = useState<DeletionQueueItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    checkAuth();
    loadAllData();
  }, []);

  const checkAuth = () => {
    const user = localStorage.getItem("user");
    if (!user) {
      router.push("/auth/login");
      return;
    }
    const userData = JSON.parse(user);
    if (userData.role !== "admin") {
      toast({
        title: "Yetkisiz Erişim",
        description: "Bu sayfaya erişim yetkiniz yok",
        variant: "destructive",
      });
      router.push("/");
    }
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([loadStats(), loadDeletionQueue(), loadAuditLogs(), loadUsers()]);
    } catch (error) {
      console.error("Failed to load KVKK data:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/kvkk/stats`, { headers: getAuthHeaders() });
      if (response.ok) {
        setStats(await response.json());
      }
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  const loadDeletionQueue = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/kvkk/deletion-queue`, { headers: getAuthHeaders() });
      if (response.ok) {
        setDeletionQueue(await response.json());
      }
    } catch (error) {
      console.error("Failed to load deletion queue:", error);
    }
  };

  const loadAuditLogs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/kvkk/audit-logs`, { headers: getAuthHeaders() });
      if (response.ok) {
        setAuditLogs(await response.json());
      }
    } catch (error) {
      console.error("Failed to load audit logs:", error);
    }
  };

  const loadUsers = async (search?: string) => {
    try {
      const url = search
        ? `${API_BASE_URL}/admin/kvkk/users?search=${encodeURIComponent(search)}`
        : `${API_BASE_URL}/admin/kvkk/users`;
      const response = await fetch(url, { headers: getAuthHeaders() });
      if (response.ok) {
        setUsers(await response.json());
      }
    } catch (error) {
      console.error("Failed to load users:", error);
    }
  };

  const handleManualCleanup = async () => {
    if (!confirm("KVKK temizlik işlemini başlatmak istediğinize emin misiniz?")) {
      return;
    }

    setCleanupLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/kvkk/manual-cleanup`, {
        method: "POST",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const result = await response.json();
        toast({
          title: "Temizlik Tamamlandı",
          description: `${result.processed} sipariş işlendi, ${result.deleted} dosya silindi.`,
        });
        loadAllData();
      } else {
        throw new Error("Cleanup failed");
      }
    } catch (error) {
      toast({
        title: "Hata",
        description: "Temizlik işlemi başarısız oldu.",
        variant: "destructive",
      });
    } finally {
      setCleanupLoading(false);
    }
  };

  const handleDeleteUser = async (userId: string, email: string | null) => {
    if (
      !confirm(
        `"${email || userId}" kullanıcısının TÜM verilerini kalıcı olarak silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz!`
      )
    ) {
      return;
    }

    setDeleteLoading(userId);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/kvkk/delete-user/${userId}`, {
        method: "POST",
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const result = await response.json();
        toast({
          title: "Kullanıcı Verileri Silindi",
          description: `${result.photos_deleted} fotoğraf, ${result.audio_deleted} ses dosyası silindi. ${result.orders_anonymized} sipariş anonimleştirildi.`,
        });
        loadAllData();
      } else {
        throw new Error("Delete failed");
      }
    } catch (error) {
      toast({
        title: "Hata",
        description: "Silme işlemi başarısız oldu.",
        variant: "destructive",
      });
    } finally {
      setDeleteLoading(null);
    }
  };

  const handleExportUser = async (userId: string, email: string | null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/kvkk/export-user-data/${userId}`, {
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const data = await response.json();
        // JSON olarak indir
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `user-data-${email || userId}-${new Date().toISOString().split("T")[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        toast({
          title: "Veri Export Edildi",
          description: "Kullanıcı verileri JSON olarak indirildi.",
        });
      } else {
        throw new Error("Export failed");
      }
    } catch (error) {
      toast({
        title: "Hata",
        description: "Export işlemi başarısız oldu.",
        variant: "destructive",
      });
    }
  };

  const handleUserSearch = () => {
    loadUsers(userSearch);
  };

  const getActionBadgeColor = (action: string) => {
    const colors: Record<string, string> = {
      KVKK_PHOTO_DELETED: "bg-red-100 text-red-800",
      USER_DATA_DELETED: "bg-red-100 text-red-800",
      USER_DATA_EXPORTED: "bg-blue-100 text-blue-800",
      MANUAL_KVKK_CLEANUP: "bg-yellow-100 text-yellow-800",
    };
    return colors[action] || "bg-gray-100 text-gray-800";
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("tr-TR", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-purple-600" />
          <p className="text-gray-600">KVKK verileri yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/admin">
              <Button variant="ghost" size="sm">
                ← Geri
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-purple-800">KVKK Yönetimi</h1>
              <p className="text-sm text-gray-500">
                Kişisel Verilerin Korunması Kanunu Uyumluluk Paneli
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            className="border-red-300 text-red-600 hover:bg-red-50"
            onClick={handleManualCleanup}
            disabled={cleanupLoading}
          >
            {cleanupLoading ? "İşleniyor..." : "Manuel Temizlik Çalıştır"}
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-5">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Toplam Kullanıcı</CardDescription>
                <CardTitle className="text-2xl">{stats.total_users}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Fotoğraflı Sipariş</CardDescription>
                <CardTitle className="text-2xl">{stats.total_orders_with_photos}</CardTitle>
              </CardHeader>
            </Card>
            <Card className="border-yellow-200 bg-yellow-50">
              <CardHeader className="pb-2">
                <CardDescription>Silinmeyi Bekleyen</CardDescription>
                <CardTitle className="text-2xl text-yellow-700">
                  {stats.pending_deletions}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card className="border-green-200 bg-green-50">
              <CardHeader className="pb-2">
                <CardDescription>Son 30 Günde Silinen</CardDescription>
                <CardTitle className="text-2xl text-green-700">
                  {stats.deleted_last_30_days}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card className="border-purple-200 bg-purple-50">
              <CardHeader className="pb-2">
                <CardDescription>Saklama Süresi</CardDescription>
                <CardTitle className="text-2xl text-purple-700">
                  {stats.kvkk_retention_days} Gün
                </CardTitle>
              </CardHeader>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="queue" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="queue">Silme Kuyruğu</TabsTrigger>
            <TabsTrigger value="users">Kullanıcılar</TabsTrigger>
            <TabsTrigger value="logs">Audit Logları</TabsTrigger>
          </TabsList>

          {/* Deletion Queue Tab */}
          <TabsContent value="queue">
            <Card>
              <CardHeader>
                <CardTitle>Otomatik Silme Kuyruğu</CardTitle>
                <CardDescription>
                  DELIVERED statüsündeki siparişlerin fotoğrafları teslimattan 30 gün sonra otomatik
                  silinir
                </CardDescription>
              </CardHeader>
              <CardContent>
                {deletionQueue.length === 0 ? (
                  <div className="py-8 text-center text-gray-500">Silinme bekleyen sipariş yok</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="px-4 py-3 text-left">Sipariş ID</th>
                          <th className="px-4 py-3 text-left">Çocuk Adı</th>
                          <th className="px-4 py-3 text-left">Teslim Tarihi</th>
                          <th className="px-4 py-3 text-left">Silinme Tarihi</th>
                          <th className="px-4 py-3 text-left">Kalan Gün</th>
                          <th className="px-4 py-3 text-left">Veriler</th>
                        </tr>
                      </thead>
                      <tbody>
                        {deletionQueue.map((item) => (
                          <tr key={item.order_id} className="border-b hover:bg-gray-50">
                            <td className="px-4 py-3 font-mono text-sm">
                              {item.order_id.substring(0, 8)}...
                            </td>
                            <td className="px-4 py-3">{item.child_name}</td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {formatDate(item.delivered_at)}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {formatDate(item.scheduled_deletion)}
                            </td>
                            <td className="px-4 py-3">
                              <Badge
                                className={
                                  item.days_remaining <= 7
                                    ? "bg-red-100 text-red-800"
                                    : item.days_remaining <= 14
                                      ? "bg-yellow-100 text-yellow-800"
                                      : "bg-gray-100 text-gray-800"
                                }
                              >
                                {item.days_remaining} gün
                              </Badge>
                            </td>
                            <td className="space-x-1 px-4 py-3">
                              {item.has_photo && (
                                <Badge variant="outline" className="text-xs">
                                  Fotoğraf
                                </Badge>
                              )}
                              {item.has_cloned_voice && (
                                <Badge variant="outline" className="text-xs">
                                  Ses
                                </Badge>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>Kullanıcı Yönetimi</CardTitle>
                    <CardDescription>
                      Unutulma Hakkı (Right to be Forgotten) ve Veri Taşınabilirliği işlemleri
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Input
                      placeholder="E-posta veya isim ara..."
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleUserSearch()}
                      className="w-64"
                    />
                    <Button onClick={handleUserSearch} variant="outline">
                      Ara
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {users.length === 0 ? (
                  <div className="py-8 text-center text-gray-500">Kullanıcı bulunamadı</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="px-4 py-3 text-left">Kullanıcı</th>
                          <th className="px-4 py-3 text-left">Kayıt Tarihi</th>
                          <th className="px-4 py-3 text-left">Sipariş</th>
                          <th className="px-4 py-3 text-left">Fotoğraf</th>
                          <th className="px-4 py-3 text-left">Durum</th>
                          <th className="px-4 py-3 text-left">İşlemler</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((user) => (
                          <tr key={user.id} className="border-b hover:bg-gray-50">
                            <td className="px-4 py-3">
                              <div className="font-medium">{user.full_name || "-"}</div>
                              <div className="text-sm text-gray-500">{user.email || "Misafir"}</div>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {formatDate(user.created_at)}
                            </td>
                            <td className="px-4 py-3 text-center">{user.orders_count}</td>
                            <td className="px-4 py-3 text-center">{user.photos_count}</td>
                            <td className="px-4 py-3">
                              <Badge
                                className={
                                  user.is_active
                                    ? "bg-green-100 text-green-800"
                                    : "bg-gray-100 text-gray-800"
                                }
                              >
                                {user.is_active ? "Aktif" : "Pasif"}
                              </Badge>
                            </td>
                            <td className="space-x-2 px-4 py-3">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleExportUser(user.id, user.email)}
                              >
                                Export
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleDeleteUser(user.id, user.email)}
                                disabled={deleteLoading === user.id}
                              >
                                {deleteLoading === user.id ? "Siliniyor..." : "Sil"}
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Audit Logs Tab */}
          <TabsContent value="logs">
            <Card>
              <CardHeader>
                <CardTitle>KVKK Audit Logları</CardTitle>
                <CardDescription>Tüm KVKK ile ilgili işlemlerin kayıtları</CardDescription>
              </CardHeader>
              <CardContent>
                {auditLogs.length === 0 ? (
                  <div className="py-8 text-center text-gray-500">Henüz KVKK log kaydı yok</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="px-4 py-3 text-left">Tarih</th>
                          <th className="px-4 py-3 text-left">İşlem</th>
                          <th className="px-4 py-3 text-left">Sipariş ID</th>
                          <th className="px-4 py-3 text-left">Kullanıcı ID</th>
                          <th className="px-4 py-3 text-left">Detaylar</th>
                        </tr>
                      </thead>
                      <tbody>
                        {auditLogs.map((log) => (
                          <tr key={log.id} className="border-b hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {formatDate(log.created_at)}
                            </td>
                            <td className="px-4 py-3">
                              <Badge className={getActionBadgeColor(log.action)}>
                                {log.action}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 font-mono text-sm">
                              {log.order_id ? `${log.order_id.substring(0, 8)}...` : "-"}
                            </td>
                            <td className="px-4 py-3 font-mono text-sm">
                              {log.user_id ? `${log.user_id.substring(0, 8)}...` : "-"}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {log.details ? (
                                <code className="rounded bg-gray-100 px-2 py-1 text-xs">
                                  {JSON.stringify(log.details).substring(0, 50)}...
                                </code>
                              ) : (
                                "-"
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Info Cards */}
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-lg text-blue-800">Otomatik Silme</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-blue-700">
              <p>
                Teslim edilen siparişlerin çocuk fotoğrafları ve klonlanmış ses kayıtları 30 gün
                sonra otomatik olarak silinir.
              </p>
              <p className="mt-2">Cron Job: Her gece 02:00</p>
            </CardContent>
          </Card>
          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-lg text-green-800">Veri Taşınabilirliği</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-green-700">
              <p>
                Kullanıcılar verilerini JSON formatında export edebilir. Export dosyası 7 gün
                geçerlidir.
              </p>
              <p className="mt-2">Fotoğraflar güvenlik nedeniyle dahil edilmez.</p>
            </CardContent>
          </Card>
          <Card className="border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="text-lg text-red-800">Unutulma Hakkı</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-red-700">
              <p>
                Kullanıcının tüm kişisel verileri silinir. Siparişler anonimleştirilerek iş
                kayıtları için tutulur.
              </p>
              <p className="mt-2 font-semibold">Bu işlem geri alınamaz!</p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
