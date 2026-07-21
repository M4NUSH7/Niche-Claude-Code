/** @type {import('next').NextConfig} */
const securityHeaders = [
  // Replace script-src with a per-request nonce for stricter CSP — see references/security.md.
  { key: "Content-Security-Policy", value: "default-src 'self'; frame-ancestors 'none'" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
];

const nextConfig = {
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
