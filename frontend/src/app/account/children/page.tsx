"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getChildren, createChild, deleteChild, type ChildProfile } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Users, Plus, Trash2, BookOpen, Loader2, X } from "lucide-react";

export default function ChildrenPage() {
  const [children, setChildren] = useState<ChildProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [age, setAge] = useState(7);
  const [gender, setGender] = useState("");
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  const fetchChildren = async () => {
    try {
      const data = await getChildren();
      setChildren(data);
    } catch {
      /* handled */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchChildren(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await createChild({ name, age, gender: gender || undefined });
      toast({ title: "Eklendi", description: `${name} başarıyla eklendi.` });
      setShowForm(false);
      setName("");
      setAge(7);
      setGender("");
      fetchChildren();
    } catch (err) {
      toast({
        title: "Hata",
        description: err instanceof Error ? err.message : "Eklenemedi",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (child: ChildProfile) => {
    const orderNote = child.order_count ? ` Bu çocuk için ${child.order_count} sipariş bulunuyor.` : "";
    if (!confirm(`${child.name} profilini silmek istediğinize emin misiniz?${orderNote}`)) return;
    try {
      await deleteChild(child.id);
      toast({ title: "Silindi", description: `${child.name} profili silindi.` });
      fetchChildren();
    } catch {
      toast({ title: "Hata", description: "Silinemedi", variant: "destructive" });
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
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900">Çocuklarım</h2>
        {children.length < 10 ? (
          <Button
            size="sm"
            className="rounded-lg bg-purple-600 text-xs hover:bg-purple-700"
            onClick={() => setShowForm(true)}
          >
            <Plus className="mr-1 h-3 w-3" />
            Çocuk Ekle
          </Button>
        ) : (
          <span className="text-xs text-gray-400">Maks. 10 profil</span>
        )}
      </div>

      {/* Add form */}
      {showForm && (
        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Yeni Çocuk Profili</h3>
            <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600">
              <X className="h-4 w-4" />
            </button>
          </div>
          <form onSubmit={handleCreate} className="grid gap-3 sm:grid-cols-3">
            <div>
              <Label className="text-xs text-gray-600">İsim</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Çocuğun adı"
                required
                minLength={2}
                className="mt-1 h-10 rounded-lg text-sm"
              />
            </div>
            <div>
              <Label className="text-xs text-gray-600">Yaş</Label>
              <Input
                type="number"
                min={1}
                max={18}
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                required
                className="mt-1 h-10 rounded-lg text-sm"
              />
            </div>
            <div>
              <Label className="text-xs text-gray-600">Cinsiyet</Label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="mt-1 h-10 w-full rounded-lg border border-gray-200 bg-white px-3 text-sm"
              >
                <option value="">Belirtilmemiş</option>
                <option value="erkek">Erkek</option>
                <option value="kız">Kız</option>
              </select>
            </div>
            <div className="sm:col-span-3">
              <Button
                type="submit"
                disabled={saving}
                className="h-10 rounded-lg bg-purple-600 text-sm hover:bg-purple-700"
              >
                {saving ? "Ekleniyor..." : "Kaydet"}
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Children list */}
      {children.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 py-16">
          <Users className="h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-base font-semibold text-gray-700">Henüz çocuk profili yok</h3>
          <p className="mt-1 text-sm text-gray-500">
            Çocuk profili ekleyerek tekrar sipariş vermeyi kolaylaştırın.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {children.map((child) => (
            <div key={child.id} className="rounded-xl border bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-purple-100 text-lg font-bold text-purple-600">
                    {child.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900">{child.name}</h4>
                    <p className="text-xs text-gray-500">
                      {child.age} yaşında
                      {child.gender && ` · ${child.gender === "erkek" ? "Erkek" : "Kız"}`}
                    </p>
                    {child.order_count > 0 && (
                      <p className="text-xs text-purple-600">{child.order_count} sipariş</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(child)}
                  className="text-gray-300 hover:text-red-500 transition-colors"
                  title="Profili sil"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="mt-3 pt-3 border-t">
                <Link href={`/create-v2?childName=${encodeURIComponent(child.name)}&childAge=${child.age}&childGender=${child.gender || ""}`}>
                  <Button variant="outline" size="sm" className="w-full rounded-lg text-xs">
                    <BookOpen className="mr-1 h-3 w-3" />
                    Yeni Masal Oluştur
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
