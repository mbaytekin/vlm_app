/** @type {import('next').NextConfig} */
const nextConfig = {
  // API proxy gerekirse buraya eklenebilir
  // Backend gateway'i doğrudan çağıracağız (CORS ayarlı)
  reactStrictMode: true,
  // Base64 data URLs kullanıyoruz, Next.js Image optimization'a gerek yok
}

module.exports = nextConfig

