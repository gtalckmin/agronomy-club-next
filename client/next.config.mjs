import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import isInsideContainer from "is-inside-container";

const projectRoot = path.dirname(fileURLToPath(import.meta.url));

const isWindowsDevContainer = () =>
  os.release().toLowerCase().includes("microsoft") && isInsideContainer();

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
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

  async rewrites() {
    return [
      {
        source: "/quizzes/download/:id",
        destination: `${process.env.NEXT_PUBLIC_BACKEND_URL}/quizzes/download/:id/`,
      },
    ];
  },

  images: {
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
