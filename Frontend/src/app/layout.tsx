import type { Metadata } from "next";
import "./globals.css";
import "leaflet/dist/leaflet.css";
import { AuthProvider } from "@/context/AuthContext";
import { BottomNav } from "@/components/layout/BottomNav";
import { MockModeBadge } from "@/components/ui/MockModeBadge";

export const metadata: Metadata = {
  title: "EcoBin Go",
  description: "Mobile-first recycling gamification app"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <div className="mx-auto flex min-h-screen max-w-md flex-col px-4 pb-24 pt-4">
            <header className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-moss/70">
                  Recycle Better
                </p>
                <h1 className="text-2xl font-semibold">EcoBin Go</h1>
              </div>
              <MockModeBadge />
            </header>
            <main className="flex-1">{children}</main>
            <BottomNav />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
