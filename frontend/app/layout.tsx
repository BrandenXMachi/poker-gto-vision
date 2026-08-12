import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'GTO Preflop Trainer',
  description: '6-max 100bb GTO preflop hand chart trainer',
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
