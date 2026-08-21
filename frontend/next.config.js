/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  headers() {
    return [
      {
        source: "/:all",
        headers: [
          // Content Security Policy
          {
            key: "Content-Security-Policy",
            value: "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-src 'none'; form-action 'self'; base-uri 'self';",
          },
          // Prevent MIME type sniffing
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          // Prevent clickjacking
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          // Enable XSS protection in older browsers
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
          // HSTS - tell browsers to only use HTTPS for this domain
          {
            key: "Strict-Transport-Security",
            value: "max-age=31536000; includeSubDomains; preload",
          },
          // Control referrer information
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
