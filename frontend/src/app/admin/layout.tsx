"use client";

import { useState, useEffect, createContext, useContext, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Package,
  BookOpen,
  Target,
  FileStack,
  ShoppingCart,
  Settings,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Bell,
  Search,
  Moon,
  Sun,
  LogOut,
  Palette,
  Shield,
  Home,
  Wand2,
  UserX,
  Ticket,
  Globe,
  Gauge,
  Users,
  BarChart3,
} from "lucide-react";

// ============ TYPES ============
interface NavItem {
  name: string;
  href?: string;
  icon: ReactNode;
  children?: NavItem[];
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

// ============ NAVIGATION CONFIG ============
const navigation: NavGroup[] = [
  {
    title: "GENEL",
    items: [
      {
        name: "Dashboard",
        href: "/admin",
        icon: <LayoutDashboard className="h-5 w-5" />,
      },
    ],
  },
  {
    title: "SİSTEM",
    items: [
      {
        name: "Ana Sayfa Yönetimi",
        href: "/admin/homepage",
        icon: <Globe className="h-5 w-5" />,
      },
      {
        name: "AI Prompt Şablonları",
        href: "/admin/prompts",
        icon: <Wand2 className="h-5 w-5" />,
      },
      {
        name: "KVKK Yönetimi",
        href: "/admin/kvkk",
        icon: <Shield className="h-5 w-5" />,
      },
      {
        name: "Rate Limit",
        href: "/admin/rate-limit",
        icon: <Gauge className="h-5 w-5" />,
      },
      {
        name: "Kullanıcılar",
        href: "/admin/users",
        icon: <Users className="h-5 w-5" />,
      },
    ],
  },
  {
    title: "KATALOG YÖNETİMİ",
    items: [
      {
        name: "Ürün Yönetimi",
        href: "/admin/products",
        icon: <Package className="h-5 w-5" />,
      },
      {
        name: "Senaryo & İçerik",
        href: "/admin/scenarios",
        icon: <BookOpen className="h-5 w-5" />,
      },
      {
        name: "Kazanımlar",
        href: "/admin/learning-outcomes",
        icon: <Target className="h-5 w-5" />,
      },
      {
        name: "Görsel Stiller",
        href: "/admin/visual-styles",
        icon: <Palette className="h-5 w-5" />,
      },
      {
        name: "Baskı Şablonları",
        href: "/admin/config",
        icon: <FileStack className="h-5 w-5" />,
      },
      {
        name: "İç Kapak Arkası",
        href: "/admin/back-cover",
        icon: <FileStack className="h-5 w-5" />,
      },
    ],
  },
  {
    title: "SATIŞ & SİPARİŞ",
    items: [
      {
        name: "Siparişler",
        href: "/admin/orders",
        icon: <ShoppingCart className="h-5 w-5" />,
      },
      {
        name: "Kupon Kodları",
        href: "/admin/promo-codes",
        icon: <Ticket className="h-5 w-5" />,
      },
      {
        name: "Terk Edilen Denemeler",
        href: "/admin/abandoned-trials",
        icon: <UserX className="h-5 w-5" />,
      },
      {
        name: "Muhasebe & Gelir",
        href: "/admin/accounting",
        icon: <BarChart3 className="h-5 w-5" />,
      },
    ],
  },
];

// ============ CONTEXT ============
interface SidebarContextType {
  isCollapsed: boolean;
  setIsCollapsed: (value: boolean) => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (value: boolean) => void;
}

const SidebarContext = createContext<SidebarContextType>({
  isCollapsed: false,
  setIsCollapsed: () => {},
  isMobileOpen: false,
  setIsMobileOpen: () => {},
});

// ============ SIDEBAR ITEM ============
function SidebarItem({ item, isCollapsed }: { item: NavItem; isCollapsed: boolean }) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const hasChildren = item.children && item.children.length > 0;
  const isActive =
    item.href === pathname || item.children?.some((child) => child.href === pathname);

  // Auto-expand if a child is active
  useEffect(() => {
    if (item.children?.some((child) => child.href === pathname)) {
      setIsOpen(true);
    }
  }, [pathname, item.children]);

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`
            flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition-all duration-200
            ${
              isActive
                ? "ml-[-4px] border-l-4 border-indigo-600 bg-indigo-50 pl-[16px] text-indigo-700"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }
          `}
        >
          <span className={`flex-shrink-0 ${isActive ? "text-indigo-600" : "text-slate-500"}`}>
            {item.icon}
          </span>
          {!isCollapsed && (
            <>
              <span className="flex-1 text-left text-sm font-medium">{item.name}</span>
              <ChevronDown
                className={`h-4 w-4 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
              />
            </>
          )}
        </button>

        <AnimatePresence initial={false}>
          {isOpen && !isCollapsed && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="ml-4 mt-1 space-y-1 border-l-2 border-slate-200 pl-3">
                {item.children?.map((child) => (
                  <SidebarItem key={child.name} item={child} isCollapsed={isCollapsed} />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <Link
      href={item.href || "#"}
      className={`
        flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all duration-200
        ${
          isActive
            ? "ml-[-4px] border-l-4 border-indigo-600 bg-indigo-50 pl-[16px] text-indigo-700"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
        }
      `}
      title={isCollapsed ? item.name : undefined}
    >
      <span className={`flex-shrink-0 ${isActive ? "text-indigo-600" : "text-slate-500"}`}>
        {item.icon}
      </span>
      {!isCollapsed && <span className="text-sm font-medium">{item.name}</span>}
    </Link>
  );
}

// ============ SIDEBAR ============
function Sidebar() {
  const { isCollapsed, setIsCollapsed, isMobileOpen, setIsMobileOpen } = useContext(SidebarContext);
  const _pathname = usePathname();

  const sidebarContent = (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div
        className={`flex items-center gap-3 border-b border-slate-200 px-4 py-5 ${isCollapsed ? "justify-center" : ""}`}
      >
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600">
          <BookOpen className="h-6 w-6 text-white" />
        </div>
        {!isCollapsed && (
          <div>
            <h1 className="font-bold text-slate-900">Benim Masalım</h1>
            <p className="text-xs text-slate-500">Yönetim Paneli</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
        {navigation.map((group) => (
          <div key={group.title}>
            {!isCollapsed && (
              <h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                {group.title}
              </h2>
            )}
            <div className="space-y-1">
              {group.items.map((item) => (
                <SidebarItem key={item.name} item={item} isCollapsed={isCollapsed} />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Collapse Button - Desktop only */}
      <div className="hidden border-t border-slate-200 p-3 lg:block">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          {isCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <>
              <ChevronLeft className="h-5 w-5" />
              <span>Daralt</span>
            </>
          )}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 80 : 260 }}
        transition={{ duration: 0.2, ease: "easeInOut" }}
        className="fixed left-0 top-0 z-40 hidden h-screen flex-col border-r border-slate-200 bg-white lg:flex"
      >
        {sidebarContent}
      </motion.aside>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
              onClick={() => setIsMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="fixed left-0 top-0 z-50 h-screen w-[280px] bg-white shadow-2xl lg:hidden"
            >
              {/* Mobile Close Button */}
              <button
                onClick={() => setIsMobileOpen(false)}
                className="absolute right-4 top-4 rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

// ============ HEADER ============
function Header() {
  const { isCollapsed: _isCollapsed, setIsMobileOpen } = useContext(SidebarContext);
  const pathname = usePathname();
  const router = useRouter();
  const [isDark, setIsDark] = useState(false);

  // Generate breadcrumbs
  const getBreadcrumbs = () => {
    const paths = pathname.split("/").filter(Boolean);
    const breadcrumbs = [{ name: "Admin", href: "/admin" }];

    const pageNames: Record<string, string> = {
      products: "Ürün Yönetimi",
      scenarios: "Senaryo & İçerik",
      "learning-outcomes": "Kazanımlar",
      "visual-styles": "Görsel Stiller",
      config: "Baskı Şablonları",
      "back-cover": "İç Kapak Arkası",
      orders: "Siparişler",
      "promo-codes": "Kupon Kodları",
      "abandoned-trials": "Terk Edilen Denemeler",
      homepage: "Ana Sayfa Yönetimi",
      prompts: "AI Prompt Şablonları",
      kvkk: "KVKK Yönetimi",
      "rate-limit": "Rate Limit",
      users: "Kullanıcılar",
      accounting: "Muhasebe & Gelir",
    };

    if (paths.length > 1) {
      const pageName = pageNames[paths[1]] || paths[1];
      breadcrumbs.push({ name: pageName, href: pathname });
    }

    return breadcrumbs;
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    router.push("/auth/login");
  };

  return (
    <header
      className={`
        sticky top-0 z-30 h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md
        transition-all duration-200
      `}
    >
      <div className="flex h-full items-center justify-between gap-4 px-4 lg:px-6">
        {/* Left Side */}
        <div className="flex items-center gap-4">
          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileOpen(true)}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Breadcrumbs */}
          <nav className="hidden items-center gap-2 text-sm sm:flex">
            <Link href="/" className="text-slate-400 hover:text-slate-600">
              <Home className="h-4 w-4" />
            </Link>
            {getBreadcrumbs().map((crumb, index) => (
              <div key={crumb.href} className="flex items-center gap-2">
                <ChevronRight className="h-4 w-4 text-slate-300" />
                <Link
                  href={crumb.href}
                  className={`
                    ${
                      index === getBreadcrumbs().length - 1
                        ? "font-medium text-slate-900"
                        : "text-slate-500 hover:text-slate-700"
                    }
                  `}
                >
                  {crumb.name}
                </Link>
              </div>
            ))}
          </nav>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-2">
          {/* Search - Hidden on mobile */}
          <div className="hidden items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 md:flex">
            <Search className="h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Ara..."
              className="w-40 bg-transparent text-sm text-slate-700 placeholder-slate-400 focus:outline-none"
            />
            <kbd className="hidden items-center gap-1 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-xs text-slate-400 lg:inline-flex">
              ⌘K
            </kbd>
          </div>

          {/* Notifications */}
          <button className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700">
            <Bell className="h-5 w-5" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500" />
          </button>

          {/* Theme Toggle */}
          <button
            onClick={() => setIsDark(!isDark)}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
          >
            {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>

          {/* User Menu */}
          <div className="flex items-center gap-3 border-l border-slate-200 pl-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-slate-700">Admin</p>
              <p className="text-xs text-slate-500">Yönetici</p>
            </div>
            <div className="group relative">
              <button className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-sm font-medium text-white">
                A
              </button>

              {/* Dropdown */}
              <div className="invisible absolute right-0 top-full mt-2 w-48 rounded-xl border border-slate-200 bg-white py-2 opacity-0 shadow-lg transition-all duration-200 group-hover:visible group-hover:opacity-100">
                <Link
                  href="/admin"
                  className="flex items-center gap-2 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <Settings className="h-4 w-4" />
                  Ayarlar
                </Link>
                <hr className="my-2 border-slate-100" />
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <LogOut className="h-4 w-4" />
                  Çıkış Yap
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

// ============ ADMIN LAYOUT ============
export default function AdminLayout({ children }: { children: ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Close mobile menu on route change
  const pathname = usePathname();
  useEffect(() => {
    setIsMobileOpen(false);
  }, [pathname]);

  // Load collapsed state from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("admin-sidebar-collapsed");
    if (saved) {
      setIsCollapsed(JSON.parse(saved));
    }
  }, []);

  // Save collapsed state
  useEffect(() => {
    localStorage.setItem("admin-sidebar-collapsed", JSON.stringify(isCollapsed));
  }, [isCollapsed]);

  return (
    <SidebarContext.Provider value={{ isCollapsed, setIsCollapsed, isMobileOpen, setIsMobileOpen }}>
      <div className="min-h-screen bg-slate-50">
        <Sidebar />

        {/* Desktop Content */}
        <div
          className="hidden min-h-screen transition-all duration-200 ease-in-out lg:block"
          style={{ marginLeft: isCollapsed ? 80 : 260 }}
        >
          <Header />
          <main className="p-6">{children}</main>
        </div>

        {/* Mobile Content */}
        <div className="min-h-screen lg:hidden">
          <Header />
          <main className="p-4">{children}</main>
        </div>
      </div>
    </SidebarContext.Provider>
  );
}
