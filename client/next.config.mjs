import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import isInsideContainer from "is-inside-container";

const projectRoot = path.dirname(fileURLToPath(import.meta.url));

const isWindowsDevContainer = () =>
  os.release().toLowerCase().includes("microsoft") && isInsideContainer();

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  reactStrictMode: true,
  experimental: {
    // Next 16.3's CLI checker cannot capture TypeScript output in this runtime.
    // TypeScript 5 still exposes the compiler API, which keeps build checks enabled.
    useTypeScriptCli: false,
  },
  turbopack: {
    root: projectRoot,
  },
  // dumb fix for windows docker
  webpack: isWindowsDevContainer()
    ? (config) => {
        config.watchOptions = {
          poll: 1000,
          aggregateTimeout: 300,
        };
        return config;
      }
    : undefined,

  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/media/**",
      },
      {
        protocol: "https",
        hostname: "media.yourapp.com",
        pathname: "/media/**",
      },
    ],
    dangerouslyAllowLocalIP: process.env.NODE_ENV !== "production",
  },
};

export default nextConfig;
