/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "cdn.watchmode.com",
      },
    ],
  },
};

module.exports = nextConfig;