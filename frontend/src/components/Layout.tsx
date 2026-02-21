import { Shield } from "lucide-react";
import { type ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16">
            <Shield className="w-8 h-8 text-primary-600 mr-3" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                shipper Lite
              </h1>
              <p className="text-xs text-gray-500">出口单证合规检查</p>
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-500 text-sm">
          © 2026 shipper Lite. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
