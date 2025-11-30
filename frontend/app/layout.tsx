import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'FEMSTAT - Gender Analysis Tool',
  description: 'Professional gender-stratified statistical analysis platform by FEMSTAT from Femanalytica',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-[#FAFAFA]">
          <header className="border-b border-[#E5E5E5] bg-white sticky top-0 z-50 shadow-sm">
            <div className="container mx-auto px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#5B197B] shadow-md">
                      <span className="text-white font-bold text-lg">♀</span>
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-[#171717]">
                        FEMANALYTICA INSIGHT
                      </h1>
                      <p className="text-xs text-[#737373] -mt-1">FEMSTAT</p>
                    </div>
                  </div>
                </div>
                <nav className="hidden md:flex items-center gap-6">
                  <a href="/" className="text-sm font-medium text-[#171717] hover:text-[#5B197B]">Dashboard</a>
                  <a href="/analysis" className="text-sm font-medium text-[#171717] hover:text-[#5B197B]">Analysis</a>
                  <a href="/reports" className="text-sm font-medium text-[#171717] hover:text-[#5B197B]">Reports</a>
                  <a href="/team" className="text-sm font-medium text-[#171717] hover:text-[#5B197B]">Team</a>
                </nav>
                <div className="flex items-center gap-3">
                  <a href="/login" className="text-sm font-medium text-[#171717] hover:text-[#5B197B]">Log In</a>
                  <a href="/signup" className="px-4 py-2 bg-[#EF4444] text-white rounded-xl text-sm font-medium hover:bg-[#DC2626] transition-colors">Sign Up</a>
                </div>
              </div>
            </div>
          </header>
          <main className="container mx-auto px-6 py-8 max-w-7xl">
            {children}
          </main>
          <footer className="border-t border-[#E5E5E5] mt-16 bg-white/50 backdrop-blur-sm">
            <div className="container mx-auto px-6 py-6">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#1A237E]">
                    <span className="text-white font-bold text-sm">F</span>
                  </div>
                  <p className="text-[#1A237E] text-sm font-semibold">FEMSTAT</p>
                </div>
                <p className="text-[#737373] text-sm text-center">
                  Professional Gender-Stratified Statistical Analysis Platform
                </p>
                <p className="text-[#737373] text-xs">
                  © {new Date().getFullYear()} FEMSTAT from Femanalytica. All rights reserved.
                </p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}

