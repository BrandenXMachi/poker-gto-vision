'use client'

import { useState } from 'react'

export default function LoginPage() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')

    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })

      if (res.ok) {
        const params = new URLSearchParams(window.location.search)
        const from = params.get('from')
        // Only allow internal redirects.
        window.location.href = from && from.startsWith('/') ? from : '/'
        return
      }

      setError('Incorrect password.')
    } catch {
      setError('Something went wrong. Try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main style={styles.wrap}>
      <form onSubmit={onSubmit} style={styles.card}>
        <h1 style={styles.title}>GTO Preflop Trainer</h1>
        <p style={styles.sub}>This site is private. Enter the password to continue.</p>

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoFocus
          autoComplete="current-password"
          style={styles.input}
        />

        <button type="submit" disabled={busy || !password} style={styles.button}>
          {busy ? 'Checking…' : 'Enter'}
        </button>

        {error ? <p style={styles.error}>{error}</p> : null}
      </form>
    </main>
  )
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#0f1115',
    padding: '1.5rem',
  },
  card: {
    width: '100%',
    maxWidth: 380,
    background: '#181b22',
    border: '1px solid #262b36',
    borderRadius: 12,
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.85rem',
    boxShadow: '0 10px 40px rgba(0,0,0,0.45)',
  },
  title: {
    margin: 0,
    color: '#f2f4f8',
    fontSize: '1.35rem',
    fontFamily: 'system-ui, sans-serif',
  },
  sub: {
    margin: '0 0 0.4rem',
    color: '#8b93a4',
    fontSize: '0.9rem',
    fontFamily: 'system-ui, sans-serif',
  },
  input: {
    padding: '0.7rem 0.85rem',
    borderRadius: 8,
    border: '1px solid #2f3644',
    background: '#0f1115',
    color: '#f2f4f8',
    fontSize: '1rem',
    outline: 'none',
  },
  button: {
    padding: '0.7rem 0.85rem',
    borderRadius: 8,
    border: 'none',
    background: '#3b82f6',
    color: '#fff',
    fontSize: '1rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  error: {
    margin: 0,
    color: '#f87171',
    fontSize: '0.88rem',
    fontFamily: 'system-ui, sans-serif',
  },
}
