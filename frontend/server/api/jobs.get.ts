export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const query = getQuery(event);

  const params = new URLSearchParams();
  if (query.q) params.set("q", String(query.q));
  if (query.source) params.set("source", String(query.source));

  const url = `${config.apiUrl}/jobs?${params}`;
  return await $fetch(url);
});
