export default defineEventHandler(async () => {
  const config = useRuntimeConfig();
  return await $fetch(`${config.apiUrl}/jobs/sync`, { method: "POST" });
});
