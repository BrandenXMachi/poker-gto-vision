import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Poker GTO Vision',
  description: 'Real-time poker GTO analysis using phone camera',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
