/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      // The trainer used to live at /gto-trainer; it is now the site root.
      {
        source: '/gto-trainer',
        destination: '/',
        permanent: true,
      },
    ]
  },
}

module.exports = nextConfig
