<template>
  <div class="container">
    <header>
      <h1>JobBoard Stockholm</h1>
      <div class="meta">
        <span v-if="data?.last_sync">
          Last sync: {{ new Date(data.last_sync).toLocaleString() }}
        </span>
      </div>
    </header>

    <div class="controls">
      <input
        v-model="search"
        type="text"
        placeholder="Search jobs (React, Vue, TypeScript...)"
        @input="debouncedRefresh"
      />
      <select v-model="source" @change="refresh()">
        <option value="">All sources</option>
        <option value="indeed">Indeed</option>
        <option value="linkedin">LinkedIn</option>
      </select>
      <button class="btn" :disabled="syncing" @click="sync">
        {{ syncing ? "Syncing..." : "Sync now" }}
      </button>
    </div>

    <p class="count">{{ data?.count ?? 0 }} jobs found</p>

    <div class="job-list">
      <div v-for="job in data?.jobs" :key="job.url" class="job-card">
        <h3>
          <a :href="job.url" target="_blank" rel="noopener">{{ job.title }}</a>
        </h3>
        <div class="job-meta">
          <span>{{ job.company }}</span>
          <span>{{ job.location }}</span>
          <span class="tag">{{ job.source }}</span>
          <span v-if="job.date_posted">{{ job.date_posted }}</span>
        </div>
        <p class="job-desc">{{ job.description }}</p>
      </div>

      <div v-if="data?.jobs?.length === 0" class="empty">
        No jobs found. Try syncing or adjusting your search.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Job {
  title: string;
  company: string;
  location: string;
  url: string;
  source: string;
  date_posted: string;
  description: string;
}

interface JobsResponse {
  count: number;
  last_sync: string | null;
  jobs: Job[];
}

const search = ref("");
const source = ref("");
const syncing = ref(false);

const { data, refresh } = await useFetch<JobsResponse>("/api/jobs", {
  query: { q: search, source },
});

let debounceTimer: ReturnType<typeof setTimeout>;
function debouncedRefresh() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => refresh(), 300);
}

async function sync() {
  syncing.value = true;
  try {
    await $fetch("/api/sync", { method: "POST" });
    // Wait a bit for scrape to start, then refresh
    setTimeout(async () => {
      await refresh();
      syncing.value = false;
    }, 3000);
  } catch {
    syncing.value = false;
  }
}
</script>
