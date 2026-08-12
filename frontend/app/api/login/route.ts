import { createHash, timingSafeEqual } from 'crypto'
import { NextRequest, NextResponse } from 'next/server'

import { AUTH_COOKIE, SALT, expectedToken } from '../../../auth-config'

export const runtime = 'nodejs'

function safeEquals(a: string, b: string): boolean {
  const bufA = Buffer.from(a)
  const bufB = Buffer.from(b)
  if (bufA.length !== bufB.length) return false
  return timingSafeEqual(bufA, bufB)
}

export async function POST(req: NextRequest) {
  let password = ''
  try {
    const body = await req.json()
    password = typeof body?.password === 'string' ? body.password : ''
  } catch {
    return NextResponse.json({ ok: false }, { status: 400 })
  }

  const token = createHash('sha256').update(password + SALT).digest('hex')

  if (!safeEquals(token, expectedToken())) {
    // Small delay to blunt rapid guessing.
    await new Promise((r) => setTimeout(r, 600))
    return NextResponse.json({ ok: false }, { status: 401 })
  }

  const res = NextResponse.json({ ok: true })
  res.cookies.set({
    name: AUTH_COOKIE,
    value: token,
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60 * 24 * 30, // 30 days
  })
  return res
}
