"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  Ticket,
  Search,
  Copy,
  Wand2,
} from "lucide-react";
import Link from "next/link";
import { API_BASE_URL } from "@/lib/api";

// ─── Types ─────────────────────────────────────────────────────

interface PromoCode {
  id: string;
  code: string;
  discount_type: "PERCENT" | "AMOUNT";
  discount_value: number;
  usage_limit: number;
  used_count: number;
  is_active: boolean;
  valid_from: string | null;
  valid_until: string | null;
  min_order_amount: number | null;
  max_discount_amount: number | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

interface FormData {
  code: string;
  discount_type: "PERCENT" | "AMOUNT";
  discount_value: string;
  usage_limit: string;
  valid_from: string;
  valid_until: string;
  min_order_amount: string;
  max_discount_amount: string;
  notes: string;
}

interface BulkFormData {
  count: string;
  discount_type: "PERCENT" | "AMOUNT";
  discount_value: string;
  usage_limit: string;
  valid_from: string;
  valid_until: string;
  min_order_amount: string;
  max_discount_amount: string;
  prefix: string;
  notes: string;
}

const defaultFormData: FormData = {
  code: "",
  discount_type: "PERCENT",
  discount_value: "",
  usage_limit: "1",
  valid_from: "",
  valid_until: "",
  min_order_amount: "",
  max_discount_amount: "",
  notes: "",
};

const defaultBulkFormData: BulkFormData = {
  count: "10",
  discount_type: "PERCENT",
  discount_value: "",
  usage_limit: "1",
  valid_from: "",
  valid_until: "",
  min_order_amount: "",
  max_discount_amount: "",
  prefix: "",
  notes: "",
};

// ─── Page ──────────────────────────────────────────────────────

export default function AdminPromoCodesPage() {
  const [promoCodes, setPromoCodes] = useState<PromoCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showBulkForm, setShowBulkForm] = useState(false);
  const [editingPromo, setEditingPromo] = useState<PromoCode | null>(null);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<FormData>(defaultFormData);
  const [bulkFormData, setBulkFormData] =
    useState<BulkFormData>(defaultBulkFormData);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterActive, setFilterActive] = useState<boolean | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    checkAuth();
    fetchPromoCodes();
  }, [currentPage, filterActive, searchQuery]);

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

  // ─── API Calls ────────────────────────────────────────────────

  const fetchPromoCodes = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/auth/login");
        return;
      }

      const params = new URLSearchParams({
        page: String(currentPage),
        page_size: String(pageSize),
      });
      if (filterActive !== null) params.set("is_active", String(filterActive));
      if (searchQuery.trim()) params.set("search", searchQuery.trim());

      const response = await fetch(
        `${API_BASE_URL}/admin/promo-codes?${params}`,
        { headers: getAuthHeaders() }
      );

      if (response.status === 401) {
        localStorage.removeItem("token");
        router.push("/auth/login");
        return;
      }

      if (response.ok) {
        const data = await response.json();
        setPromoCodes(data.items);
        setTotalCount(data.total);
      } else {
        toast({
          title: "Hata",
          description: "Kupon kodları yüklenemedi",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Hata",
        description: "Bağlantı hatası",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.discount_value || Number(formData.discount_value) <= 0) {
      toast({
        title: "Hata",
        description: "İndirim değeri girilmelidir",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        discount_type: formData.discount_type,
        discount_value: Number(formData.discount_value),
        usage_limit: Number(formData.usage_limit) || 1,
      };

      if (formData.code.trim()) payload.code = formData.code.trim();
      if (formData.valid_from) payload.valid_from = new Date(formData.valid_from).toISOString();
      if (formData.valid_until) payload.valid_until = new Date(formData.valid_until).toISOString();
      if (formData.min_order_amount)
        payload.min_order_amount = Number(formData.min_order_amount);
      if (formData.max_discount_amount)
        payload.max_discount_amount = Number(formData.max_discount_amount);
      if (formData.notes.trim()) payload.notes = formData.notes.trim();

      const url = editingPromo
        ? `${API_BASE_URL}/admin/promo-codes/${editingPromo.id}`
        : `${API_BASE_URL}/admin/promo-codes`;

      const response = await fetch(url, {
        method: editingPromo ? "PATCH" : "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: editingPromo
            ? "Kupon kodu güncellendi"
            : "Kupon kodu oluşturuldu",
        });
        setShowForm(false);
        resetForm();
        fetchPromoCodes();
      } else {
        const err = await response.json().catch(() => null);
        toast({
          title: "Hata",
          description: err?.detail || "İşlem başarısız oldu",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Hata",
        description: "Bağlantı hatası",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleBulkGenerate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (
      !bulkFormData.discount_value ||
      Number(bulkFormData.discount_value) <= 0
    ) {
      toast({
        title: "Hata",
        description: "İndirim değeri girilmelidir",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        count: Number(bulkFormData.count) || 10,
        discount_type: bulkFormData.discount_type,
        discount_value: Number(bulkFormData.discount_value),
        usage_limit: Number(bulkFormData.usage_limit) || 1,
      };

      if (bulkFormData.prefix.trim())
        payload.prefix = bulkFormData.prefix.trim();
      if (bulkFormData.valid_from)
        payload.valid_from = new Date(bulkFormData.valid_from).toISOString();
      if (bulkFormData.valid_until)
        payload.valid_until = new Date(bulkFormData.valid_until).toISOString();
      if (bulkFormData.min_order_amount)
        payload.min_order_amount = Number(bulkFormData.min_order_amount);
      if (bulkFormData.max_discount_amount)
        payload.max_discount_amount = Number(bulkFormData.max_discount_amount);
      if (bulkFormData.notes.trim())
        payload.notes = bulkFormData.notes.trim();

      const response = await fetch(
        `${API_BASE_URL}/admin/promo-codes/bulk-generate`,
        {
          method: "POST",
          headers: getAuthHeaders(),
          body: JSON.stringify(payload),
        }
      );

      if (response.ok) {
        const data = await response.json();
        toast({
          title: "Başarılı",
          description: `${data.count} adet kupon kodu oluşturuldu`,
        });
        setShowBulkForm(false);
        setBulkFormData(defaultBulkFormData);
        fetchPromoCodes();
      } else {
        const err = await response.json().catch(() => null);
        toast({
          title: "Hata",
          description: err?.detail || "Toplu üretim başarısız",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Hata",
        description: "Bağlantı hatası",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (promoId: string) => {
    if (!confirm("Bu kupon kodunu deaktif etmek istediğinize emin misiniz?"))
      return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/promo-codes/${promoId}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: "Kupon kodu deaktif edildi",
        });
        fetchPromoCodes();
      } else {
        toast({
          title: "Hata",
          description: "İşlem başarısız oldu",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Hata",
        description: "Bağlantı hatası",
        variant: "destructive",
      });
    }
  };

  const handleToggleActive = async (promo: PromoCode) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/promo-codes/${promo.id}`,
        {
          method: "PATCH",
          headers: getAuthHeaders(),
          body: JSON.stringify({ is_active: !promo.is_active }),
        }
      );

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: promo.is_active
            ? "Kupon deaktif edildi"
            : "Kupon aktif edildi",
        });
        fetchPromoCodes();
      }
    } catch {
      toast({
        title: "Hata",
        description: "İşlem başarısız",
        variant: "destructive",
      });
    }
  };

  // ─── Helpers ──────────────────────────────────────────────────

  const resetForm = () => {
    setFormData(defaultFormData);
    setEditingPromo(null);
  };

  const handleEdit = (promo: PromoCode) => {
    setFormData({
      code: promo.code,
      discount_type: promo.discount_type,
      discount_value: String(promo.discount_value),
      usage_limit: String(promo.usage_limit),
      valid_from: promo.valid_from
        ? new Date(promo.valid_from).toISOString().slice(0, 16)
        : "",
      valid_until: promo.valid_until
        ? new Date(promo.valid_until).toISOString().slice(0, 16)
        : "",
      min_order_amount: promo.min_order_amount
        ? String(promo.min_order_amount)
        : "",
      max_discount_amount: promo.max_discount_amount
        ? String(promo.max_discount_amount)
        : "",
      notes: promo.notes || "",
    });
    setEditingPromo(promo);
    setShowForm(true);
    setShowBulkForm(false);
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast({ title: "Kopyalandı", description: `${code} panoya kopyalandı` });
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("tr-TR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  const formatDiscount = (promo: PromoCode) => {
    if (promo.discount_type === "PERCENT") {
      return `%${promo.discount_value}`;
    }
    return `${promo.discount_value} TL`;
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  // ─── Render ───────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/admin">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Kupon Kodları</h1>
            <p className="text-sm text-muted-foreground">
              Toplam {totalCount} kupon kodu
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              setShowBulkForm(true);
              setShowForm(false);
            }}
          >
            <Wand2 className="h-4 w-4 mr-2" />
            Toplu Üret
          </Button>
          <Button
            onClick={() => {
              resetForm();
              setShowForm(true);
              setShowBulkForm(false);
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Yeni Kupon
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <Label>Kod Ara</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Kupon kodu ara..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant={filterActive === null ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setFilterActive(null);
                  setCurrentPage(1);
                }}
              >
                Tümü
              </Button>
              <Button
                variant={filterActive === true ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setFilterActive(true);
                  setCurrentPage(1);
                }}
              >
                Aktif
              </Button>
              <Button
                variant={filterActive === false ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setFilterActive(false);
                  setCurrentPage(1);
                }}
              >
                Pasif
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create / Edit Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>
              {editingPromo ? "Kuponu Düzenle" : "Yeni Kupon Kodu"}
            </CardTitle>
            <CardDescription>
              {editingPromo
                ? `${editingPromo.code} kuponunu düzenliyorsunuz`
                : "Kod boş bırakılırsa otomatik üretilir"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Code */}
                {!editingPromo && (
                  <div>
                    <Label>Kupon Kodu (opsiyonel)</Label>
                    <Input
                      placeholder="Boş bırakın = otomatik üretilir"
                      value={formData.code}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          code: e.target.value.toUpperCase(),
                        })
                      }
                      maxLength={50}
                    />
                  </div>
                )}

                {/* Discount Type */}
                <div>
                  <Label>İndirim Tipi</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={formData.discount_type}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        discount_type: e.target.value as "PERCENT" | "AMOUNT",
                      })
                    }
                  >
                    <option value="PERCENT">Yüzde (%)</option>
                    <option value="AMOUNT">Sabit Tutar (TL)</option>
                  </select>
                </div>

                {/* Discount Value */}
                <div>
                  <Label>
                    İndirim Değeri{" "}
                    {formData.discount_type === "PERCENT" ? "(%)" : "(TL)"}
                  </Label>
                  <Input
                    type="number"
                    placeholder={
                      formData.discount_type === "PERCENT" ? "1-100" : "Tutar"
                    }
                    value={formData.discount_value}
                    onChange={(e) =>
                      setFormData({ ...formData, discount_value: e.target.value })
                    }
                    min={formData.discount_type === "PERCENT" ? 1 : 0.01}
                    max={formData.discount_type === "PERCENT" ? 100 : undefined}
                    step="0.01"
                    required
                  />
                </div>

                {/* Usage Limit */}
                <div>
                  <Label>Kullanım Limiti</Label>
                  <Input
                    type="number"
                    placeholder="1"
                    value={formData.usage_limit}
                    onChange={(e) =>
                      setFormData({ ...formData, usage_limit: e.target.value })
                    }
                    min={1}
                    required
                  />
                </div>

                {/* Valid From */}
                <div>
                  <Label>Başlangıç Tarihi (opsiyonel)</Label>
                  <Input
                    type="datetime-local"
                    value={formData.valid_from}
                    onChange={(e) =>
                      setFormData({ ...formData, valid_from: e.target.value })
                    }
                  />
                </div>

                {/* Valid Until */}
                <div>
                  <Label>Bitiş Tarihi (opsiyonel)</Label>
                  <Input
                    type="datetime-local"
                    value={formData.valid_until}
                    onChange={(e) =>
                      setFormData({ ...formData, valid_until: e.target.value })
                    }
                  />
                </div>

                {/* Min Order Amount */}
                <div>
                  <Label>Minimum Sipariş Tutarı (opsiyonel)</Label>
                  <Input
                    type="number"
                    placeholder="0"
                    value={formData.min_order_amount}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        min_order_amount: e.target.value,
                      })
                    }
                    min={0}
                    step="0.01"
                  />
                </div>

                {/* Max Discount Amount */}
                <div>
                  <Label>Maksimum İndirim Tutarı (opsiyonel)</Label>
                  <Input
                    type="number"
                    placeholder="Tavan indirim"
                    value={formData.max_discount_amount}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        max_discount_amount: e.target.value,
                      })
                    }
                    min={0}
                    step="0.01"
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <Label>Notlar (opsiyonel)</Label>
                <Textarea
                  placeholder="Admin notları..."
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData({ ...formData, notes: e.target.value })
                  }
                  rows={2}
                />
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving && "Kaydediliyor..."}
                  {!saving && editingPromo && "Güncelle"}
                  {!saving && !editingPromo && "Oluştur"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowForm(false);
                    resetForm();
                  }}
                >
                  İptal
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Bulk Generate Form */}
      {showBulkForm && (
        <Card>
          <CardHeader>
            <CardTitle>Toplu Kupon Üretimi</CardTitle>
            <CardDescription>
              Aynı ayarlarla birden fazla kupon kodu üretin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleBulkGenerate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Count */}
                <div>
                  <Label>Adet</Label>
                  <Input
                    type="number"
                    value={bulkFormData.count}
                    onChange={(e) =>
                      setBulkFormData({ ...bulkFormData, count: e.target.value })
                    }
                    min={1}
                    max={100}
                    required
                  />
                </div>

                {/* Prefix */}
                <div>
                  <Label>Ön Ek (opsiyonel)</Label>
                  <Input
                    placeholder="KAMPANYA"
                    value={bulkFormData.prefix}
                    onChange={(e) =>
                      setBulkFormData({
                        ...bulkFormData,
                        prefix: e.target.value.toUpperCase(),
                      })
                    }
                    maxLength={10}
                  />
                </div>

                {/* Discount Type */}
                <div>
                  <Label>İndirim Tipi</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={bulkFormData.discount_type}
                    onChange={(e) =>
                      setBulkFormData({
                        ...bulkFormData,
                        discount_type: e.target.value as "PERCENT" | "AMOUNT",
                      })
                    }
                  >
                    <option value="PERCENT">Yüzde (%)</option>
                    <option value="AMOUNT">Sabit Tutar (TL)</option>
                  </select>
                </div>

                {/* Discount Value */}
                <div>
                  <Label>
                    İndirim Değeri{" "}
                    {bulkFormData.discount_type === "PERCENT" ? "(%)" : "(TL)"}
                  </Label>
                  <Input
                    type="number"
                    value={bulkFormData.discount_value}
                    onChange={(e) =>
                      setBulkFormData({
                        ...bulkFormData,
                        discount_value: e.target.value,
                      })
                    }
                    min={bulkFormData.discount_type === "PERCENT" ? 1 : 0.01}
                    max={
                      bulkFormData.discount_type === "PERCENT" ? 100 : undefined
                    }
                    step="0.01"
                    required
                  />
                </div>

                {/* Usage Limit */}
                <div>
                  <Label>Her Kuponun Kullanım Limiti</Label>
                  <Input
                    type="number"
                    value={bulkFormData.usage_limit}
                    onChange={(e) =>
                      setBulkFormData({
                        ...bulkFormData,
                        usage_limit: e.target.value,
                      })
                    }
                    min={1}
                    required
                  />
                </div>

                {/* Valid From */}
                <div>
                  <Label>Başlangıç Tarihi (opsiyonel)</Label>
                  <Input
                    type="datetime-local"
                    value={bulkFormData.valid_from}
                    onChange={(e) =>
                      setBulkFormData({
                        ...bulkFormData,
                        valid_from: e.target.value,
                      })
                    }
                  />
                </div>

                {/* Valid Until */}
                <div>
                  <Label>Bitiş Tarihi (opsiyonel)</Label>
                  <Input
                    type="datetime-local"
                    value={bulkFormData.valid_until}
                    onChange={(e) =>
                      setBulkFormData({
                        ...bulkFormData,
                        valid_until: e.target.value,
                      })
                    }
                  />
                </div>

                {/* Max Discount Amount */}
                <div>
                  <Label>Maks İndirim Tutarı (opsiyonel)</Label>
                  <Input
                    type="number"
                    placeholder="Tavan indirim"
                    value={bulkFormData.max_discount_amount}
                    onChange={(e) =>
                      setBulkFormData({
                        ...bulkFormData,
                        max_discount_amount: e.target.value,
                      })
                    }
                    min={0}
                    step="0.01"
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <Label>Notlar (opsiyonel)</Label>
                <Textarea
                  placeholder="Admin notları..."
                  value={bulkFormData.notes}
                  onChange={(e) =>
                    setBulkFormData({ ...bulkFormData, notes: e.target.value })
                  }
                  rows={2}
                />
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving ? "Üretiliyor..." : "Toplu Üret"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowBulkForm(false);
                    setBulkFormData(defaultBulkFormData);
                  }}
                >
                  İptal
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Table */}
      <Card>
        <CardContent className="pt-6">
          {promoCodes.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Ticket className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Henüz kupon kodu bulunmuyor</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-3 font-medium">Kod</th>
                    <th className="pb-3 font-medium">İndirim</th>
                    <th className="pb-3 font-medium">Kullanım</th>
                    <th className="pb-3 font-medium">Durum</th>
                    <th className="pb-3 font-medium">Geçerlilik</th>
                    <th className="pb-3 font-medium">Min. Tutar</th>
                    <th className="pb-3 font-medium text-right">İşlemler</th>
                  </tr>
                </thead>
                <tbody>
                  {promoCodes.map((promo) => (
                    <tr
                      key={promo.id}
                      className="border-b last:border-0 hover:bg-muted/50"
                    >
                      {/* Code */}
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <code className="font-mono font-bold text-sm bg-muted px-2 py-0.5 rounded">
                            {promo.code}
                          </code>
                          <button
                            onClick={() => copyCode(promo.code)}
                            className="text-muted-foreground hover:text-foreground"
                            title="Kopyala"
                          >
                            <Copy className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>

                      {/* Discount */}
                      <td className="py-3">
                        <Badge variant="secondary">
                          {formatDiscount(promo)}
                        </Badge>
                        {promo.max_discount_amount && (
                          <span className="text-xs text-muted-foreground ml-1">
                            (maks {promo.max_discount_amount} TL)
                          </span>
                        )}
                      </td>

                      {/* Usage */}
                      <td className="py-3">
                        <span
                          className={
                            promo.used_count >= promo.usage_limit
                              ? "text-red-600 font-medium"
                              : ""
                          }
                        >
                          {promo.used_count} / {promo.usage_limit}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={promo.is_active}
                            onCheckedChange={() => handleToggleActive(promo)}
                          />
                          <Badge
                            variant={promo.is_active ? "default" : "outline"}
                          >
                            {promo.is_active ? "Aktif" : "Pasif"}
                          </Badge>
                        </div>
                      </td>

                      {/* Validity */}
                      <td className="py-3 text-xs">
                        {promo.valid_from || promo.valid_until ? (
                          <>
                            {formatDate(promo.valid_from)} -{" "}
                            {formatDate(promo.valid_until)}
                          </>
                        ) : (
                          <span className="text-muted-foreground">
                            Süresiz
                          </span>
                        )}
                      </td>

                      {/* Min Amount */}
                      <td className="py-3">
                        {promo.min_order_amount
                          ? `${promo.min_order_amount} TL`
                          : "-"}
                      </td>

                      {/* Actions */}
                      <td className="py-3 text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(promo)}
                            title="Düzenle"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          {promo.is_active && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDelete(promo.id)}
                              title="Deaktif Et"
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Sayfa {currentPage} / {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => p - 1)}
                >
                  Önceki
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((p) => p + 1)}
                >
                  Sonraki
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
