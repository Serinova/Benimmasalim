"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Phone,
  Mail,
  User,
  Baby,
  BookOpen,
  Image,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  RefreshCw,
  MessageSquare,
  Eye,
  TrendingUp,
  UserX,
  DollarSign,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";

interface AbandonedTrial {
  id: string;
  parent_name: string;
  parent_email: string;
  parent_phone: string | null;
  child_name: string;
  child_age: number;
  story_title: string;
  story_pages: Array<{ page_number: number; text: string }>;
  preview_images: Record<string, string>;
  product_name: string | null;
  product_price: number | null;
  created_at: string;
  preview_shown_at: string | null;
  abandoned_at: string | null;
  followed_up_at: string | null;
  followed_up_by: string | null;
  follow_up_notes: string | null;
}

interface TrialStats {
  total_leads: number;
  preview_generated: number;
  converted: number;
  abandoned: number;
  pending_followup: number;
  conversion_rate: number;
}

export default function AbandonedTrialsPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [trials, setTrials] = useState<AbandonedTrial[]>([]);
  const [stats, setStats] = useState<TrialStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTrial, setSelectedTrial] = useState<AbandonedTrial | null>(null);
  const [showFollowUpDialog, setShowFollowUpDialog] = useState(false);
  const [showStoryDialog, setShowStoryDialog] = useState(false);
  const [followUpNotes, setFollowUpNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [includeFollowedUp, setIncludeFollowedUp] = useState(false);

  useEffect(() => {
    fetchData();
  }, [includeFollowedUp]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");

      // Fetch trials
      const trialsRes = await fetch(
        `${API_BASE_URL}/admin/trials/abandoned?include_followed_up=${includeFollowedUp}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (trialsRes.ok) {
        const trialsData = await trialsRes.json();
        setTrials(trialsData);
      }

      // Fetch stats
      const statsRes = await fetch(`${API_BASE_URL}/admin/trials/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast({
        title: "Hata",
        description: "Veriler yüklenemedi",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFollowUp = async () => {
    if (!selectedTrial) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${API_BASE_URL}/admin/trials/abandoned/${selectedTrial.id}/follow-up`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ notes: followUpNotes }),
        }
      );

      if (response.ok) {
        toast({
          title: "Başarılı",
          description: "Takip kaydedildi",
        });
        setShowFollowUpDialog(false);
        setFollowUpNotes("");
        fetchData();
      } else {
        throw new Error("Takip kaydedilemedi");
      }
    } catch (error) {
      toast({
        title: "Hata",
        description: "Takip kaydedilemedi",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString("tr-TR");
  };

  const getTimeSince = (dateStr: string | null) => {
    if (!dateStr) return "-";
    const diff = Date.now() - new Date(dateStr).getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 24) return `${hours} saat önce`;
    const days = Math.floor(hours / 24);
    return `${days} gün önce`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => router.push("/admin")}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Admin Panel
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Terk Edilmiş Denemeler</h1>
              <p className="text-gray-600">
                Önizleme gördü ama satın almadı - Potansiyel müşteriler
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setIncludeFollowedUp(!includeFollowedUp)}>
              {includeFollowedUp ? "Takip Edilenleri Gizle" : "Takip Edilenleri Göster"}
            </Button>
            <Button onClick={fetchData} disabled={loading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Yenile
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-5">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
                    <User className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Toplam Lead</p>
                    <p className="text-2xl font-bold">{stats.total_leads}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100">
                    <Eye className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Önizleme Gördü</p>
                    <p className="text-2xl font-bold">{stats.preview_generated}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                    <DollarSign className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Satın Aldı</p>
                    <p className="text-2xl font-bold">{stats.converted}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
                    <UserX className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Terk Etti</p>
                    <p className="text-2xl font-bold">{stats.abandoned}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100">
                    <TrendingUp className="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Dönüşüm Oranı</p>
                    <p className="text-2xl font-bold">{stats.conversion_rate}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Pending Follow-up Alert */}
        {stats && stats.pending_followup > 0 && (
          <Card className="mb-6 border-amber-200 bg-amber-50">
            <CardContent className="py-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <span className="font-medium text-amber-800">
                  {stats.pending_followup} müşteri takip bekliyor!
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Trials List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : trials.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <CheckCircle2 className="mx-auto mb-4 h-12 w-12 text-green-500" />
              <p className="text-gray-600">Terk edilmiş deneme yok!</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {trials.map((trial) => (
              <motion.div
                key={trial.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className={trial.followed_up_at ? "opacity-60" : ""}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      {/* Left: Contact & Story Info */}
                      <div className="grid flex-1 grid-cols-1 gap-6 md:grid-cols-3">
                        {/* Contact Info */}
                        <div>
                          <h3 className="mb-2 flex items-center gap-2 font-semibold text-gray-900">
                            <User className="h-4 w-4" />
                            İletişim Bilgileri
                          </h3>
                          <div className="space-y-1 text-sm">
                            <p className="font-medium">{trial.parent_name}</p>
                            <p className="flex items-center gap-1 text-gray-600">
                              <Mail className="h-3 w-3" />
                              {trial.parent_email}
                            </p>
                            {trial.parent_phone && (
                              <p className="flex items-center gap-1 text-gray-600">
                                <Phone className="h-3 w-3" />
                                <a
                                  href={`tel:${trial.parent_phone}`}
                                  className="text-blue-600 hover:underline"
                                >
                                  {trial.parent_phone}
                                </a>
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Story Info */}
                        <div>
                          <h3 className="mb-2 flex items-center gap-2 font-semibold text-gray-900">
                            <BookOpen className="h-4 w-4" />
                            Hikaye
                          </h3>
                          <div className="space-y-1 text-sm">
                            <p className="font-medium">{trial.story_title}</p>
                            <p className="flex items-center gap-1 text-gray-600">
                              <Baby className="h-3 w-3" />
                              {trial.child_name} ({trial.child_age} yaş)
                            </p>
                            {trial.product_name && (
                              <p className="text-gray-600">
                                {trial.product_name} - {trial.product_price}₺
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Preview Images */}
                        <div>
                          <h3 className="mb-2 flex items-center gap-2 font-semibold text-gray-900">
                            {/* eslint-disable-next-line jsx-a11y/alt-text -- Lucide icon, decorative */}
                            <Image className="h-4 w-4" aria-hidden />
                            Görseller ({Object.keys(trial.preview_images).length} adet)
                          </h3>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(trial.preview_images).length > 0 ? (
                              Object.entries(trial.preview_images)
                                .slice(0, 6)
                                .map(([pageNum, url]) => (
                                  <img
                                    key={pageNum}
                                    src={url as string}
                                    alt={`Sayfa ${pageNum}`}
                                    className="h-20 w-20 cursor-pointer rounded-lg border object-cover transition-opacity hover:opacity-80"
                                    onClick={() => window.open(url as string, "_blank")}
                                  />
                                ))
                            ) : (
                              <p className="text-sm italic text-gray-400">Görsel yok</p>
                            )}
                            {Object.keys(trial.preview_images).length > 6 && (
                              <div className="flex h-20 w-20 items-center justify-center rounded-lg border bg-gray-100 text-sm text-gray-500">
                                +{Object.keys(trial.preview_images).length - 6}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Right: Actions & Status */}
                      <div className="ml-6 text-right">
                        <div className="mb-4 space-y-2">
                          {trial.followed_up_at ? (
                            <Badge
                              variant="outline"
                              className="border-green-200 bg-green-50 text-green-700"
                            >
                              <CheckCircle2 className="mr-1 h-3 w-3" />
                              Takip Edildi
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="border-red-200 bg-red-50 text-red-700"
                            >
                              <AlertCircle className="mr-1 h-3 w-3" />
                              Takip Bekliyor
                            </Badge>
                          )}
                          <p className="text-xs text-gray-500">
                            <Clock className="mr-1 inline h-3 w-3" />
                            {getTimeSince(trial.abandoned_at)}
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedTrial(trial);
                              setShowFollowUpDialog(true);
                            }}
                          >
                            <MessageSquare className="mr-1 h-4 w-4" />
                            {trial.followed_up_at ? "Not Ekle" : "Takip Et"}
                          </Button>

                          {trial.parent_phone && (
                            <Button size="sm" className="bg-green-600 hover:bg-green-700" asChild>
                              <a href={`tel:${trial.parent_phone}`}>
                                <Phone className="mr-1 h-4 w-4" />
                                Ara
                              </a>
                            </Button>
                          )}
                        </div>

                        {trial.followed_up_at && (
                          <p className="mt-2 text-xs text-gray-500">
                            {trial.followed_up_by} tarafından
                            <br />
                            {formatDate(trial.followed_up_at)}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Hikaye Detayı Butonu */}
                    <div className="mt-4 border-t pt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => {
                          setSelectedTrial(trial);
                          setShowStoryDialog(true);
                        }}
                      >
                        <BookOpen className="mr-2 h-4 w-4" />
                        Hikaye Detayını Gör ({trial.story_pages?.length || 0} sayfa)
                      </Button>
                    </div>

                    {/* Follow-up Notes */}
                    {trial.follow_up_notes && (
                      <div className="mt-4 rounded-lg bg-gray-50 p-3">
                        <p className="text-sm text-gray-600">
                          <MessageSquare className="mr-1 inline h-3 w-3" />
                          {trial.follow_up_notes}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}

        {/* Follow-up Dialog */}
        <Dialog open={showFollowUpDialog} onOpenChange={setShowFollowUpDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Takip Kaydı</DialogTitle>
            </DialogHeader>

            {selectedTrial && (
              <div className="space-y-4">
                <div className="rounded-lg bg-gray-50 p-4">
                  <p className="font-medium">{selectedTrial.parent_name}</p>
                  <p className="text-sm text-gray-600">{selectedTrial.parent_phone}</p>
                  <p className="text-sm text-gray-600">{selectedTrial.story_title}</p>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium">Notlar (Görüşme özeti)</label>
                  <Textarea
                    value={followUpNotes}
                    onChange={(e) => setFollowUpNotes(e.target.value)}
                    placeholder="Müşteriyle görüşme notları..."
                    rows={4}
                  />
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowFollowUpDialog(false)}>
                İptal
              </Button>
              <Button onClick={handleFollowUp} disabled={submitting}>
                {submitting ? "Kaydediliyor..." : "Kaydet"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Story Detail Dialog */}
        <Dialog open={showStoryDialog} onOpenChange={setShowStoryDialog}>
          <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                {selectedTrial?.story_title}
              </DialogTitle>
            </DialogHeader>

            {selectedTrial && (
              <div className="space-y-6">
                {/* Bilgi Özeti */}
                <div className="grid grid-cols-2 gap-4 rounded-lg bg-gray-50 p-4 md:grid-cols-4">
                  <div>
                    <p className="text-xs text-gray-500">Ebeveyn</p>
                    <p className="font-medium">{selectedTrial.parent_name}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Çocuk</p>
                    <p className="font-medium">
                      {selectedTrial.child_name} ({selectedTrial.child_age} yaş)
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">İletişim</p>
                    <p className="font-medium">
                      {selectedTrial.parent_phone || selectedTrial.parent_email}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Ürün</p>
                    <p className="font-medium">
                      {selectedTrial.product_name || "-"}{" "}
                      {selectedTrial.product_price ? `(${selectedTrial.product_price}₺)` : ""}
                    </p>
                  </div>
                </div>

                {/* Tüm Görseller */}
                {Object.keys(selectedTrial.preview_images).length > 0 && (
                  <div>
                    <h3 className="mb-3 flex items-center gap-2 font-semibold">
                      {/* eslint-disable-next-line jsx-a11y/alt-text -- Lucide icon, decorative */}
                      <Image className="h-4 w-4" aria-hidden />
                      Tüm Görseller ({Object.keys(selectedTrial.preview_images).length})
                    </h3>
                    <div className="grid grid-cols-4 gap-2 md:grid-cols-6">
                      {Object.entries(selectedTrial.preview_images)
                        .sort(([a], [b]) => parseInt(a) - parseInt(b))
                        .map(([pageNum, url]) => (
                          <div key={pageNum} className="group relative">
                            <img
                              src={url as string}
                              alt={`Sayfa ${pageNum}`}
                              className="aspect-square w-full cursor-pointer rounded-lg border object-cover transition-opacity hover:opacity-80"
                              onClick={() => window.open(url as string, "_blank")}
                            />
                            <span className="absolute bottom-1 left-1 rounded bg-black/60 px-1.5 py-0.5 text-xs text-white">
                              {parseInt(pageNum) + 1}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Hikaye Sayfaları */}
                {selectedTrial.story_pages && selectedTrial.story_pages.length > 0 && (
                  <div>
                    <h3 className="mb-3 flex items-center gap-2 font-semibold">
                      <BookOpen className="h-4 w-4" />
                      Hikaye Metni ({selectedTrial.story_pages.length} sayfa)
                    </h3>
                    <div className="max-h-[400px] space-y-4 overflow-y-auto pr-2">
                      {selectedTrial.story_pages.map(
                        (
                          page: { page_number: number; text: string; visual_prompt?: string },
                          index: number
                        ) => (
                          <div key={index} className="rounded-lg border bg-white p-4">
                            <div className="mb-2 flex items-center gap-2">
                              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-purple-100 text-xs font-bold text-purple-700">
                                {page.page_number + 1}
                              </span>
                              <span className="text-sm text-gray-500">
                                Sayfa {page.page_number + 1}
                              </span>
                            </div>
                            <p className="whitespace-pre-wrap text-gray-800">{page.text}</p>
                            {page.visual_prompt && (
                              <details className="mt-3">
                                <summary className="cursor-pointer text-xs text-blue-600 hover:underline">
                                  {`Görsel Prompt\u2019u Göster`}
                                </summary>
                                <p className="mt-2 rounded bg-gray-50 p-2 text-xs text-gray-500">
                                  {page.visual_prompt}
                                </p>
                              </details>
                            )}
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowStoryDialog(false)}>
                Kapat
              </Button>
              {selectedTrial?.parent_phone && (
                <Button className="bg-green-600 hover:bg-green-700" asChild>
                  <a href={`tel:${selectedTrial.parent_phone}`}>
                    <Phone className="mr-2 h-4 w-4" />
                    Müşteriyi Ara
                  </a>
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
