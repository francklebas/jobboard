import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",
  ssr: true,
  app: {
    head: {
      title: "JobBoard Stockholm",
      meta: [
        { name: "description", content: "Frontend jobs in Stockholm" },
      ],
    },
  },
  runtimeConfig: {
    apiUrl: process.env.NITRO_API_URL || "http://localhost:8000",
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || "http://localhost:8000",
    },
  },
  css: ["~/assets/main.css"],
  vite: {
    plugins: [tailwindcss()],
  },
});
