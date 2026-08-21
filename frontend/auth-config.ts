/**
 * Shared auth constants.
 *
 * NOTE: this repository is PUBLIC, so the password is never stored here in
 * plaintext. Only a salted SHA-256 hash of it is committed. That hash is also
 * what gets stored in the session cookie, so the middleware can validate a
 * session by simple comparison without hashing on the edge runtime.
 *
 * To rotate the password without changing code, set SITE_PASSWORD_HASH in the
 * Render dashboard to a new sha256(password + SALT) value:
 *
 *   node -e "console.log(require('crypto').createHash('sha256').update('NEWPASS'+'lelabubu-gto-v1').digest('hex'))"
 *
 * This file deliberately lives outside lib/, which is covered by .gitignore.
 */

export const AUTH_COOKIE = 'lelabubu_auth'

export const SALT = 'lelabubu-gto-v1'

/** sha256('<password>' + SALT) */
const DEFAULT_HASH =
  '4100cc6c18389514a35481bb514b5953d856e28f6dd07ccb0e4ed054e1fb1a6e'

export function expectedToken(): string {
  return process.env.SITE_PASSWORD_HASH || DEFAULT_HASH
}
