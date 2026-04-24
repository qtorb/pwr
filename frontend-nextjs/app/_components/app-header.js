"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Home", isActive: (pathname) => pathname === "/" },
  { href: "/projects", label: "Projects", isActive: (pathname) => pathname.startsWith("/projects") },
  { href: "/tasks", label: "Tasks", isActive: (pathname) => pathname.startsWith("/tasks") },
  {
    href: "/observatory",
    label: "Observatory",
    isActive: (pathname) => pathname.startsWith("/observatory"),
  },
];

export default function AppHeader({
  subtitle,
  statusText = "API conectada",
  statusTone = "ok",
}) {
  const pathname = usePathname();

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <div className="topbar-main">
          <div className="brand-block">
            <Link href="/" className="brand">
              PWR
            </Link>
            <div className="subtle">{subtitle}</div>
          </div>

          <nav className="topbar-nav" aria-label="Primary">
            {NAV_ITEMS.map((item) => {
              const active = item.isActive(pathname);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-link${active ? " active" : ""}`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className={`status-chip${statusTone === "ok" ? " ok" : ""}`}>{statusText}</div>
      </div>
    </header>
  );
}
