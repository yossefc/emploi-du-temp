import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import clsx from "clsx";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import { useTheme } from "@/hooks/useTheme";
import { Button } from "@/components/ui/Button";

interface NavItem {
  to: string;
  label: string;
}

const NAV_ITEMS: { key: keyof Record<string, string>; to: string }[] = [
  { key: "wizard", to: "/wizard" },
  { key: "schools", to: "/schools" },
  { key: "grades", to: "/grades" },
  { key: "classes", to: "/classes" },
  { key: "subjects", to: "/subjects" },
  { key: "teachers", to: "/teachers" },
  { key: "rooms", to: "/rooms" },
  { key: "groups", to: "/groups" },
  { key: "constraints", to: "/constraints" },
  { key: "schedules", to: "/schedules" },
];

export function AppShell() {
  const { t, i18n } = useTranslation();
  const { theme, setTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  const items: NavItem[] = NAV_ITEMS.map(({ key, to }) => ({
    to,
    label: t(`nav.${String(key)}`),
  }));

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      {/* Top bar */}
      <header className="sticky top-0 z-30 border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl">📅</span>
            <span className="font-semibold text-slate-900 dark:text-slate-100">
              {t("app.title")}
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <select
              value={i18n.language}
              onChange={(e) => i18n.changeLanguage(e.target.value)}
              className="rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-sm"
              aria-label="Language"
            >
              <option value="fr">FR</option>
              <option value="he">עב</option>
            </select>
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value as typeof theme)}
              className="rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-sm"
              aria-label="Theme"
            >
              <option value="system">{t("common.theme.system")}</option>
              <option value="light">{t("common.theme.light")}</option>
              <option value="dark">{t("common.theme.dark")}</option>
            </select>
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setMobileOpen((v) => !v)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? (
                <XMarkIcon className="h-5 w-5" />
              ) : (
                <Bars3Icon className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-7xl flex-1 gap-6 px-4 py-6">
        {/* Sidebar */}
        <aside
          className={clsx(
            "fixed inset-x-0 top-[57px] bottom-0 z-20 overflow-y-auto bg-white dark:bg-slate-900 px-4 py-6 lg:static lg:block lg:w-60 lg:shrink-0 lg:px-0 lg:py-0",
            mobileOpen ? "block" : "hidden lg:block"
          )}
        >
          <nav className="flex flex-col gap-1">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  clsx(
                    "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main */}
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
