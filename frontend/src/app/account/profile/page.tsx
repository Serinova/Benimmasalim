"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getUserProfile, updateProfile, changePassword,
  getAddresses, createAddress, deleteAddress, setDefaultAddress,
  getNotificationPrefs, updateNotificationPrefs,
  exportData, deleteAccount,
  type UserProfile, type UserAddress, type NotificationPrefs,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import {
  User, Lock, MapPin, Bell, Shield, Loader2,
  Plus, Trash2, Star, Download, AlertTriangle, Eye, EyeOff, X,
} from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const { toast } = useToast();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [addresses, setAddresses] = useState<UserAddress[]>([]);
  const [prefs, setPrefs] = useState<NotificationPrefs | null>(null);
  const [loading, setLoading] = useState(true);

  // Profile edit
  const [editName, setEditName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  // Password change
  const [showPwForm, setShowPwForm] = useState(false);
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [savingPw, setSavingPw] = useState(false);

  // Address form
  const [showAddrForm, setShowAddrForm] = useState(false);
  const [addrForm, setAddrForm] = useState({
    label: "Ev", full_name: "", phone: "", address_line: "", city: "", district: "", postal_code: "",
  });
  const [savingAddr, setSavingAddr] = useState(false);

  // Export data
  const [exporting, setExporting] = useState(false);

  // Account deletion
  const [showDeleteForm, setShowDeleteForm] = useState(false);
  const [deletePw, setDeletePw] = useState("");
  const [deleteReason, setDeleteReason] = useState("");

  useEffect(() => {
    Promise.all([
      getUserProfile().then((p) => { setProfile(p); setEditName(p.full_name || ""); setEditPhone(p.phone || ""); }),
      getAddresses().then(setAddresses),
      getNotificationPrefs().then(setPrefs),
    ]).finally(() => setLoading(false));
  }, []);

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      const updated = await updateProfile({ full_name: editName, phone: editPhone || undefined });
      setProfile(updated);
      localStorage.setItem("user", JSON.stringify(updated));
      toast({ title: "Kaydedildi", description: "Profil bilgileriniz güncellendi." });
    } catch (e) {
      toast({ title: "Hata", description: e instanceof Error ? e.message : "Kaydedilemedi", variant: "destructive" });
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPw(true);
    try {
      await changePassword(currentPw, newPw);
      toast({ title: "Başarılı", description: "Şifreniz değiştirildi." });
      setShowPwForm(false);
      setCurrentPw("");
      setNewPw("");
    } catch (err) {
      toast({ title: "Hata", description: err instanceof Error ? err.message : "Değiştirilemedi", variant: "destructive" });
    } finally {
      setSavingPw(false);
    }
  };

  const handleCreateAddress = async (e: React.FormEvent) => {
    e.preventDefault();

    if (addrForm.phone && !/^0[5]\d{9}$/.test(addrForm.phone.replace(/\s/g, ""))) {
      toast({ title: "Hata", description: "Geçerli bir telefon numarası girin (05XX XXX XX XX)", variant: "destructive" });
      return;
    }
    if (addrForm.postal_code && !/^\d{5}$/.test(addrForm.postal_code)) {
      toast({ title: "Hata", description: "Posta kodu 5 haneli olmalıdır", variant: "destructive" });
      return;
    }

    setSavingAddr(true);
    try {
      await createAddress({ ...addrForm, is_default: addresses.length === 0 });
      setAddresses(await getAddresses());
      setShowAddrForm(false);
      setAddrForm({ label: "Ev", full_name: "", phone: "", address_line: "", city: "", district: "", postal_code: "" });
      toast({ title: "Eklendi", description: "Adres eklendi." });
    } catch (err) {
      toast({ title: "Hata", description: err instanceof Error ? err.message : "Eklenemedi", variant: "destructive" });
    } finally {
      setSavingAddr(false);
    }
  };

  const handleDeleteAddress = async (id: string) => {
    try {
      await deleteAddress(id);
      setAddresses(await getAddresses());
    } catch { /* handled */ }
  };

  const handleSetDefault = async (id: string) => {
    const prev = addresses;
    setAddresses(addresses.map((a) => ({ ...a, is_default: a.id === id })));
    try {
      await setDefaultAddress(id);
    } catch {
      setAddresses(prev);
    }
  };

  const handleTogglePref = async (key: keyof NotificationPrefs) => {
    if (!prefs) return;
    const updated = { ...prefs, [key]: !prefs[key] };
    setPrefs(updated);
    try {
      await updateNotificationPrefs({ [key]: updated[key] });
    } catch {
      setPrefs(prefs);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const data = await exportData();
      const json = JSON.stringify(data, null, 2);
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "benimmasalim-verilerim.json";
      a.click();
      URL.revokeObjectURL(url);
      toast({ title: "İndirildi", description: "Verileriniz indirildi." });
    } catch {
      toast({ title: "Hata", description: "Veriler indirilemedi. Lütfen tekrar deneyin.", variant: "destructive" });
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!confirm("Hesabınız 7 gün içinde kalıcı olarak silinecek. Emin misiniz?")) return;
    try {
      await deleteAccount(deletePw, deleteReason || undefined);
      toast({ title: "Hesap silme talebi alındı", description: "7 gün içinde hesabınız silinecektir." });
      localStorage.clear();
      router.replace("/");
    } catch (err) {
      toast({ title: "Hata", description: err instanceof Error ? err.message : "İşlem başarısız", variant: "destructive" });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-20 sm:pb-6">
      {/* Profile info */}
      <section className="rounded-xl border bg-white p-5">
        <div className="flex items-center gap-2 mb-4">
          <User className="h-4 w-4 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-700">Kişisel Bilgiler</h3>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <Label className="text-xs text-gray-600">Ad Soyad</Label>
            <Input value={editName} onChange={(e) => setEditName(e.target.value)} className="mt-1 h-10 rounded-lg text-sm" />
          </div>
          <div>
            <Label className="text-xs text-gray-600">Telefon</Label>
            <Input value={editPhone} onChange={(e) => setEditPhone(e.target.value)} placeholder="05XX XXX XX XX" className="mt-1 h-10 rounded-lg text-sm" />
          </div>
          <div className="sm:col-span-2">
            <Label className="text-xs text-gray-600">E-posta</Label>
            <Input value={profile?.email || ""} disabled className="mt-1 h-10 rounded-lg text-sm bg-gray-50" />
          </div>
        </div>
        <Button onClick={handleSaveProfile} disabled={savingProfile} size="sm" className="mt-4 rounded-lg bg-purple-600 text-xs hover:bg-purple-700">
          {savingProfile ? "Kaydediliyor..." : "Kaydet"}
        </Button>
      </section>

      {/* Password */}
      <section className="rounded-xl border bg-white p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-gray-500" />
            <h3 className="text-sm font-semibold text-gray-700">Şifre</h3>
          </div>
          {!showPwForm && (
            <Button variant="outline" size="sm" className="rounded-lg text-xs" onClick={() => setShowPwForm(true)}>
              Şifre Değiştir
            </Button>
          )}
        </div>
        {showPwForm && (
          <form onSubmit={handleChangePassword} className="space-y-3">
            <div>
              <Label className="text-xs text-gray-600">Mevcut Şifre</Label>
              <Input type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)} required className="mt-1 h-10 rounded-lg text-sm" />
            </div>
            <div>
              <Label className="text-xs text-gray-600">Yeni Şifre</Label>
              <div className="relative mt-1">
                <Input type={showPw ? "text" : "password"} value={newPw} onChange={(e) => setNewPw(e.target.value)} required minLength={8} className="h-10 rounded-lg pr-10 text-sm" />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" tabIndex={-1}>
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={savingPw} size="sm" className="rounded-lg bg-purple-600 text-xs hover:bg-purple-700">
                {savingPw ? "Değiştiriliyor..." : "Değiştir"}
              </Button>
              <Button type="button" variant="outline" size="sm" className="rounded-lg text-xs" onClick={() => setShowPwForm(false)}>
                İptal
              </Button>
            </div>
          </form>
        )}
      </section>

      {/* Addresses */}
      <section className="rounded-xl border bg-white p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-gray-500" />
            <h3 className="text-sm font-semibold text-gray-700">Adres Defteri</h3>
          </div>
          {addresses.length < 5 && (
            <Button variant="outline" size="sm" className="rounded-lg text-xs" onClick={() => setShowAddrForm(true)}>
              <Plus className="mr-1 h-3 w-3" /> Ekle
            </Button>
          )}
          {addresses.length >= 5 && (
            <span className="text-xs text-gray-400">Maks. 5 adres</span>
          )}
        </div>

        {showAddrForm && (
          <form onSubmit={handleCreateAddress} className="mb-4 rounded-lg border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-600">Yeni Adres</span>
              <button type="button" onClick={() => setShowAddrForm(false)}><X className="h-4 w-4 text-gray-400" /></button>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              <Input placeholder="Etiket (Ev, İş...)" value={addrForm.label} onChange={(e) => setAddrForm({ ...addrForm, label: e.target.value })} className="h-9 rounded-lg text-sm" />
              <Input placeholder="Ad Soyad" value={addrForm.full_name} onChange={(e) => setAddrForm({ ...addrForm, full_name: e.target.value })} required className="h-9 rounded-lg text-sm" />
              <Input placeholder="Telefon" value={addrForm.phone} onChange={(e) => setAddrForm({ ...addrForm, phone: e.target.value })} className="h-9 rounded-lg text-sm" />
              <Input placeholder="Şehir" value={addrForm.city} onChange={(e) => setAddrForm({ ...addrForm, city: e.target.value })} required className="h-9 rounded-lg text-sm" />
              <Input placeholder="İlçe" value={addrForm.district} onChange={(e) => setAddrForm({ ...addrForm, district: e.target.value })} className="h-9 rounded-lg text-sm" />
              <Input placeholder="Posta Kodu" value={addrForm.postal_code} onChange={(e) => setAddrForm({ ...addrForm, postal_code: e.target.value })} className="h-9 rounded-lg text-sm" />
            </div>
            <Input placeholder="Adres satırı" value={addrForm.address_line} onChange={(e) => setAddrForm({ ...addrForm, address_line: e.target.value })} required className="h-9 rounded-lg text-sm" />
            <Button type="submit" disabled={savingAddr} size="sm" className="rounded-lg bg-purple-600 text-xs hover:bg-purple-700">
              {savingAddr ? "Ekleniyor..." : "Kaydet"}
            </Button>
          </form>
        )}

        {addresses.length === 0 ? (
          <p className="text-xs text-gray-400">Henüz adres eklenmemiş.</p>
        ) : (
          <div className="space-y-2">
            {addresses.map((a) => (
              <div key={a.id} className="flex items-start justify-between rounded-lg border p-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-gray-700">{a.label}</span>
                    {a.is_default && (
                      <span className="inline-flex items-center gap-0.5 rounded-full bg-purple-50 px-2 py-0.5 text-[10px] font-medium text-purple-600">
                        <Star className="h-2.5 w-2.5" /> Varsayılan
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {a.full_name} · {a.address_line}, {a.district && `${a.district}, `}{a.city}
                  </p>
                </div>
                <div className="flex gap-1">
                  {!a.is_default && (
                    <button onClick={() => handleSetDefault(a.id)} className="text-gray-300 hover:text-purple-500" title="Varsayılan yap">
                      <Star className="h-4 w-4" />
                    </button>
                  )}
                  <button onClick={() => handleDeleteAddress(a.id)} className="text-gray-300 hover:text-red-500" title="Sil">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Notification preferences */}
      {prefs && (
        <section className="rounded-xl border bg-white p-5">
          <div className="flex items-center gap-2 mb-4">
            <Bell className="h-4 w-4 text-gray-500" />
            <h3 className="text-sm font-semibold text-gray-700">Bildirim Tercihleri</h3>
          </div>
          <div className="space-y-3">
            {[
              { key: "email_order_updates" as const, label: "Sipariş güncellemeleri (e-posta)", desc: "Ödeme, üretim, kargo bildirimleri" },
              { key: "email_marketing" as const, label: "Kampanya ve haberler", desc: "Yeni senaryolar, indirimler" },
              { key: "sms_order_updates" as const, label: "SMS bildirimleri", desc: "Kargo ve teslimat SMS'leri" },
            ].map((item) => (
              <label key={item.key} className="flex items-center justify-between cursor-pointer">
                <div>
                  <p className="text-sm text-gray-700">{item.label}</p>
                  <p className="text-xs text-gray-400">{item.desc}</p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={prefs[item.key]}
                  onClick={() => handleTogglePref(item.key)}
                  className={`relative h-6 w-11 rounded-full transition-colors ${prefs[item.key] ? "bg-purple-600" : "bg-gray-200"}`}
                >
                  <span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${prefs[item.key] ? "translate-x-5" : ""}`} />
                </button>
              </label>
            ))}
          </div>
        </section>
      )}

      {/* KVKK / Privacy */}
      <section className="rounded-xl border bg-white p-5">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="h-4 w-4 text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-700">Gizlilik & KVKK</h3>
        </div>
        <div className="space-y-3">
          <Button variant="outline" size="sm" className="rounded-lg text-xs" onClick={handleExport} disabled={exporting}>
            {exporting ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Download className="mr-1 h-3 w-3" />}
            {exporting ? "Hazırlanıyor..." : "Verilerimi İndir"}
          </Button>

          {!showDeleteForm ? (
            <Button
              variant="outline"
              size="sm"
              className="rounded-lg text-xs text-red-600 border-red-200 hover:bg-red-50"
              onClick={() => setShowDeleteForm(true)}
            >
              <AlertTriangle className="mr-1 h-3 w-3" /> Hesabımı Sil
            </Button>
          ) : (
            <form onSubmit={handleDeleteAccount} className="rounded-lg border border-red-200 bg-red-50 p-4 space-y-3">
              <p className="text-xs text-red-700 font-medium">
                Hesabınız 7 gün içinde kalıcı olarak silinecek. Bu işlem geri alınamaz.
              </p>
              <Input type="password" placeholder="Şifrenizi girin" value={deletePw} onChange={(e) => setDeletePw(e.target.value)} required className="h-9 rounded-lg text-sm" />
              <Input placeholder="Silme nedeniniz (opsiyonel)" value={deleteReason} onChange={(e) => setDeleteReason(e.target.value)} className="h-9 rounded-lg text-sm" />
              <div className="flex gap-2">
                <Button type="submit" size="sm" variant="destructive" className="rounded-lg text-xs">
                  Hesabımı Sil
                </Button>
                <Button type="button" variant="outline" size="sm" className="rounded-lg text-xs" onClick={() => setShowDeleteForm(false)}>
                  İptal
                </Button>
              </div>
            </form>
          )}
        </div>
      </section>
    </div>
  );
}
