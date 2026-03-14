export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const query = getQuery(event);
  const params = new URLSearchParams();
  if (query.q) params.set("q", String(query.q));
  return await $fetch(`${config.apiUrl}/jobs/sync?${params}`, {
    method: "POST",
  });
});
