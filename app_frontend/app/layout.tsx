import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'
import { AuthProvider } from '@/contexts/AuthContext' // Added

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Application Tracker',
  description: 'Track your job applications efficiently',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={\`\${inter.className} flex flex-col min-h-screen\`}>
        <AuthProvider> {/* Added AuthProvider here */}
          <Navbar />
          <main className="flex-grow container mx-auto px-4 py-8">
            {children}
          </main>
          <Footer />
        </AuthProvider> {/* Added AuthProvider here */}
      </body>
    </html>
  )
}
