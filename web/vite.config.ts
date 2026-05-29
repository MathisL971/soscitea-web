import path from "node:path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const base = env.VITE_BASE_PATH || "/";

  return {
    base,
    plugins: [react()],
    resolve: {
      alias: {
        "@data": path.resolve(__dirname, "../data"),
      },
    },
    server: {
      fs: {
        allow: [path.resolve(__dirname, "..")],
      },
    },
  };
});
