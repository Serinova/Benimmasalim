/** @type {import('next').NextConfig} */
const backendUrl = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

const isProd = process.env.NODE_ENV === "production";

const cspDirectives = [
  "default-src 'self'",
  // Next.js requires 'unsafe-inline' for styles; nonce-based CSP needs custom server
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  // Scripts: self + inline for Next.js hydration
  `script-src 'self'${isProd ? "" : " 'unsafe-eval'"} 'unsafe-inline'`,
  "img-src 'self' data: blob: https://storage.googleapis.com https://*.googleusercontent.com",
  "font-src 'self' https://fonts.gstatic.com",
  "connect-src 'self' " + (backendUrl ? backendUrl.replace(/\/$/, "") + " " : "") + "https://storage.googleapis.com https://*.iyzipay.com https://*.google-analytics.com",
  "frame-src 'self' https://*.iyzipay.com",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self' https://*.iyzipay.com",
  "frame-ancestors 'none'",
  "upgrade-insecure-requests",
].join("; ");

const securityHeaders = [
  { key: "X-DNS-Prefetch-Control", value: "on" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(self)" },
  { key: "X-XSS-Protection", value: "1; mode=block" },
  { key: "Content-Security-Policy", value: cspDirectives },
];

const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  productionBrowserSourceMaps: false,
  poweredByHeader: false,

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },

  async rewrites() {
    return [
      { source: "/favicon.ico", destination: "/favicon.svg" },
      { source: "/health", destination: `${backendUrl}/health` },
    ];
  },

  images: {
    dangerouslyAllowSVG: true,
    contentDispositionType: "attachment",
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    remotePatterns: [
      {
        protocol: "https",
        hostname: "storage.googleapis.com",
      },
      {
        protocol: "https",
        hostname: "*.googleusercontent.com",
      },
    ],
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  experimental: {
    serverActions: {
      allowedOrigins: [
        "localhost:3000",
        "localhost:3001",
        "benimmasalim.com.tr",
        "www.benimmasalim.com.tr",
        "benimmasalim.com",
        "www.benimmasalim.com",
      ],
    },
  },
};

module.exports = nextConfig;
