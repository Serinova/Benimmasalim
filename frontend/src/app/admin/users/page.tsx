"use client";

import { useState, useEffect, useCallback } from "react";
import { Users as UsersIcon, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { useAdminAuth } from "@/hooks/use-admin-auth";
import { adminListUsers, type AdminUserItem } from "@/lib/api";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useAdminAuth();

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminListUsers({ page, page_size: 20, search: search || undefined });
      setUsers(res.items);
      setTotal(res.total);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Liste alınamadı.";
      toast({
        title: "Hata",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [page, search, toast]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const pageSize = 20;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Kullanıcılar</h1>
        <p className="mt-1 text-slate-500">Kayıtlı kullanıcıları listele ve yönet.</p>
      </div>

      <Card className="border-0 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="text-lg">Kullanıcı listesi</CardTitle>
            <CardDescription>E-posta veya ad ile arayabilirsiniz.</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="Ara..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && loadUsers()}
                className="w-56 pl-9"
              />
            </div>
            <Button variant="outline" size="sm" onClick={() => loadUsers()}>
              Ara
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
            </div>
          )}
          {!loading && users.length === 0 && (
            <div className="py-12 text-center text-slate-500">
              <UsersIcon className="mx-auto mb-4 h-12 w-12 text-slate-300" />
              <p>Kullanıcı bulunamadı.</p>
            </div>
          )}
          {!loading && users.length > 0 && (
            <>
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-slate-700">E-posta</th>
                      <th className="px-4 py-3 text-left font-medium text-slate-700">Ad Soyad</th>
                      <th className="px-4 py-3 text-left font-medium text-slate-700">Rol</th>
                      <th className="px-4 py-3 text-left font-medium text-slate-700">Durum</th>
                      <th className="px-4 py-3 text-left font-medium text-slate-700">Kayıt</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {users.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 text-slate-900">{u.email ?? "—"}</td>
                        <td className="px-4 py-3 text-slate-700">{u.full_name ?? "—"}</td>
                        <td className="px-4 py-3">
                          <span
                            className={
                              u.role === "admin"
                                ? "rounded bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700"
                                : "rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
                            }
                          >
                            {u.role}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {u.is_active ? (
                            <span className="text-emerald-600">Aktif</span>
                          ) : (
                            <span className="text-slate-400">Pasif</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-500">
                          {u.created_at ? new Date(u.created_at).toLocaleDateString("tr-TR") : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-slate-500">
                    Toplam {total} kullanıcı • Sayfa {page} / {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => p - 1)}
                    >
                      Önceki
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Sonraki
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
