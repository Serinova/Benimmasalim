"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ShoppingCart,
  Clock,
  CheckCircle2,
  TrendingUp,
  Package,
  BookOpen,
  Target,
  Palette,
  ArrowRight,
  Eye,
  UserX,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { API_BASE_URL } from "@/lib/api";
import { getAdminHeaders as getAuthHeaders } from "@/lib/adminFetch";

interface StoryPreview {
  id: string;
  status: string;
  parent_name: string;
  parent_email: string;
  child_name: string;
  child_age: number;
  story_title: string;
  product_name: string | null;
  product_price: number | null;
  page_count: number;
  page_images: { [key: string]: string } | null;
  confirmed_at: string | null;
  created_at: string;
}

interface Stats {
  total_orders: number;
  pending_orders: number;
  confirmed_orders: number;
  total_revenue: number;
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function AdminDashboard() {
  const [orders, setOrders] = useState<StoryPreview[]>([]);
  const [stats, setStats] = useState<Stats>({
    total_orders: 0,
    pending_orders: 0,
    confirmed_orders: 0,
    total_revenue: 0,
  });
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    checkAuth();
    fetchOrders();
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


  const fetchOrders = async () => {
    try {
      // Fetch stats from dedicated endpoint
      const statsRes = await fetch(`${API_BASE_URL}/admin/orders/stats/previews`, {
        headers: getAuthHeaders(),
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats({
          total_orders: statsData.total ?? 0,
          pending_orders: statsData.pending ?? 0,
          confirmed_orders: statsData.confirmed ?? 0,
          total_revenue: statsData.total_revenue ?? 0,
        });
      }

      // Fetch recent previews
      const response = await fetch(`${API_BASE_URL}/admin/orders/previews`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const raw = await response.json();
        const data: StoryPreview[] = Array.isArray(raw) ? raw : (raw.items ?? []);
        setOrders(data);
      } else {
        toast({
          title: "Veri alınamadı",
          description: `Backend ${response.status} döndü. Lütfen backend'in çalıştığından emin olun.`,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Failed to fetch orders:", error);
      toast({
        title: "Backend'e bağlanılamadı",
        description: "API sunucusu yanıt vermiyor. Docker/backend çalışıyor mu kontrol edin.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      PENDING: "bg-amber-100 text-amber-700 border-amber-200",
      CONFIRMED: "bg-emerald-100 text-emerald-700 border-emerald-200",
      EXPIRED: "bg-slate-100 text-slate-600 border-slate-200",
      CANCELLED: "bg-red-100 text-red-700 border-red-200",
    };
    return colors[status] || "bg-slate-100 text-slate-700";
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      PENDING: "Beklemede",
      CONFIRMED: "Onaylandı",
      EXPIRED: "Süresi Doldu",
      CANCELLED: "İptal",
    };
    return labels[status] || status;
  };

  const statCards = [
    {
      title: "Toplam Sipariş",
      value: stats.total_orders,
      icon: <ShoppingCart className="h-6 w-6" />,
      color: "from-blue-500 to-blue-600",
      bgColor: "bg-blue-50",
      textColor: "text-blue-600",
    },
    {
      title: "Bekleyen Onay",
      value: stats.pending_orders,
      icon: <Clock className="h-6 w-6" />,
      color: "from-amber-500 to-amber-600",
      bgColor: "bg-amber-50",
      textColor: "text-amber-600",
    },
    {
      title: "Onaylanan",
      value: stats.confirmed_orders,
      icon: <CheckCircle2 className="h-6 w-6" />,
      color: "from-emerald-500 to-emerald-600",
      bgColor: "bg-emerald-50",
      textColor: "text-emerald-600",
    },
    {
      title: "Toplam Gelir",
      value: `${stats.total_revenue.toLocaleString("tr-TR")} ₺`,
      icon: <TrendingUp className="h-6 w-6" />,
      color: "from-indigo-500 to-indigo-600",
      bgColor: "bg-indigo-50",
      textColor: "text-indigo-600",
    },
  ];

  const quickActions = [
    {
      title: "Terk Edilen Denemeler",
      description: "Satın almayan potansiyel müşteriler",
      href: "/admin/abandoned-trials",
      icon: <UserX className="h-5 w-5" />,
      color: "bg-red-500",
    },
    {
      title: "Ürün Yönetimi",
      description: "Kitap türleri ve fiyatlar",
      href: "/admin/products",
      icon: <Package className="h-5 w-5" />,
      color: "bg-violet-500",
    },
    {
      title: "Senaryolar",
      description: "Hikaye temaları",
      href: "/admin/scenarios",
      icon: <BookOpen className="h-5 w-5" />,
      color: "bg-pink-500",
    },
    {
      title: "Kazanımlar",
      description: "Eğitici içerikler",
      href: "/admin/learning-outcomes",
      icon: <Target className="h-5 w-5" />,
      color: "bg-emerald-500",
    },
    {
      title: "Görsel Stiller",
      description: "Çizim tarzları",
      href: "/admin/visual-styles",
      icon: <Palette className="h-5 w-5" />,
      color: "bg-orange-500",
    },
    {
      title: "Prompt Şablonları",
      description: "AI prompt yönetimi",
      href: "/admin/prompts",
      icon: <FileText className="h-5 w-5" />,
      color: "bg-cyan-500",
    },
  ];

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
      {/* Page Header */}
      <motion.div variants={item}>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="mt-1 text-slate-500">Hoş geldiniz! İşte bugünün özeti.</p>
      </motion.div>

      {/* Stats Grid */}
      <motion.div variants={item} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="relative overflow-hidden border-0 shadow-sm transition-shadow hover:shadow-md">
              <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-5`} />
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-500">{stat.title}</p>
                    <p className={`mt-1 text-2xl font-bold ${stat.textColor}`}>
                      {typeof stat.value === "number" ? stat.value.toLocaleString() : stat.value}
                    </p>
                  </div>
                  <div className={`${stat.bgColor} rounded-xl p-3`}>
                    <span className={stat.textColor}>{stat.icon}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Orders - Takes 2 columns */}
        <motion.div variants={item} className="lg:col-span-2">
          <Card className="border-0 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <div>
                <CardTitle className="text-lg font-semibold">Son Siparişler</CardTitle>
                <CardDescription>En son gelen sipariş talepleri</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/admin/orders")}
                className="gap-2"
              >
                Tümünü Gör
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
                </div>
              ) : orders.length === 0 ? (
                <div className="py-12 text-center">
                  <ShoppingCart className="mx-auto mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-slate-500">Henüz sipariş yok</p>
                  <p className="mt-1 text-sm text-slate-400">
                    Kullanıcılar hikaye oluşturup onayladığında burada görünecek
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {orders.slice(0, 5).map((order, index) => (
                    <motion.div
                      key={order.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="group flex items-center justify-between rounded-xl bg-slate-50 p-4 transition-colors hover:bg-slate-100"
                    >
                      <div className="flex items-center gap-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 font-medium text-white">
                          {order.child_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{order.story_title}</p>
                          <p className="text-sm text-slate-500">
                            {order.child_name} ({order.child_age} yaş) • {order.parent_email}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span
                          className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getStatusColor(order.status)}`}
                        >
                          {getStatusLabel(order.status)}
                        </span>
                        <span className="font-semibold text-slate-900">
                          {order.product_price ? `${order.product_price} ₺` : "-"}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="opacity-0 transition-opacity group-hover:opacity-100"
                          onClick={() => router.push(`/admin/orders?selected=${order.id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Quick Actions - Takes 1 column */}
        <motion.div variants={item}>
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-semibold">Hızlı Erişim</CardTitle>
              <CardDescription>Sık kullanılan sayfalar</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {quickActions.map((action, index) => (
                <motion.div
                  key={action.title}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link href={action.href}>
                    <div className="group flex items-center gap-4 rounded-xl p-4 transition-colors hover:bg-slate-50">
                      <div className={`${action.color} rounded-lg p-2.5 text-white`}>
                        {action.icon}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-slate-900 transition-colors group-hover:text-indigo-600">
                          {action.title}
                        </p>
                        <p className="text-sm text-slate-500">{action.description}</p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-slate-400 transition-all group-hover:translate-x-1 group-hover:text-indigo-600" />
                    </div>
                  </Link>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
