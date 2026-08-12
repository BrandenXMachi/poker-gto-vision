import { NextRequest, NextResponse } from 'next/server'

import { AUTH_COOKIE, expectedToken } from './auth-config'

/**
 * Server-side gate for the whole site.
 *
 * This runs before any route OR static asset in public/ is served, which is the
 * point: it protects the chart JSON under /gto-trainer/data/ as well as the
 * pages. A client-side password prompt would not, since anyone could fetch the
 * data files directly.
 */
export function middleware(req: NextRequest) {
  const token = req.cookies.get(AUTH_COOKIE)?.value

  if (token && token === expectedToken()) {
    return NextResponse.next()
  }

  const url = req.nextUrl.clone()
  url.pathname = '/login'
  url.searchParams.set('from', req.nextUrl.pathname)
  return NextResponse.redirect(url)
}

export const config = {
  /*
   * Everything is gated except:
   *  - /login            the gate itself
   *  - /api/login        the endpoint that checks the password
   *  - /_next/*          build output (contains no chart data)
   *  - favicon.ico
   */
  matcher: ['/((?!login|api/login|_next/static|_next/image|favicon.ico).*)'],
}
