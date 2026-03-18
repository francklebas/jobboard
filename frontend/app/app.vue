<template>
  <div class="max-w-4xl mx-auto p-6">
    <header class="mb-6">
      <h1 class="text-3xl font-bold mb-2">JobBoard Stockholm</h1>
      <div class="text-sm" style="color: var(--text-dim)">
        <span v-if="data?.last_sync">
          Last sync: {{ new Date(data.last_sync).toLocaleString() }}
        </span>
      </div>
    </header>

    <div class="flex flex-wrap gap-4 mb-4 items-center">
      <div class="flex gap-2">
        <input
          v-model="search"
          type="text"
          placeholder="Search jobs (React, Vue, TypeScript...)"
          class="border rounded px-3 py-2"
          style="background: var(--surface); border-color: var(--border); color: var(--text)"
          @keyup.enter="sync"
        />
        <button 
          class="px-4 py-2 rounded text-white disabled:bg-gray-400" 
          style="background: var(--accent)"
          :disabled="syncing" 
          @click="sync"
        >
          {{ syncing ? "Searching..." : "Search" }}
        </button>
      </div>

      <select v-model="source" @change="refresh()" class="border rounded px-3 py-2" style="background: var(--surface); border-color: var(--border); color: var(--text)">
        <option value="">All sources</option>
        <option value="indeed">Indeed</option>
        <option value="linkedin">LinkedIn</option>
      </select>

      <button 
        class="px-3 py-2 rounded text-white disabled:bg-gray-400 disabled:cursor-not-allowed" 
        style="background: var(--text-dim)"
        :disabled="syncing" 
        @click="sync"
      >
        {{ syncing ? "Syncing..." : "Sync Now" }}
      </button>
    </div>

    <div class="flex flex-wrap gap-2 items-center mb-5">
      <span class="text-sm" style="color: var(--text-dim)">Quick Search:</span>
      <button 
        v-for="term in ['React developer', 'Vue developer', 'TypeScript developer', 'Frontend developer']"
        :key="term"
        class="border-none px-2 py-1 rounded-full text-sm cursor-pointer"
        style="background: var(--tag-bg); color: var(--tag-text)"
        @click="quickSearch(term)"
      >
        {{ term.split(' ')[0] }}
      </button>
    </div>

    <div class="flex flex-wrap gap-3 items-center mb-6">
      <span class="text-sm" style="color: var(--text-dim)">Filter by:</span>
      <button
        v-for="f in ['all', 'new', 'viewed', 'applied', 'rejected']"
        :key="f"
        class="border px-3 py-2 rounded cursor-pointer"
        style="background: var(--surface); border-color: var(--border); color: var(--text)"
        :class="{ '!bg-[var(--accent)] !text-white !border-[var(--accent)]': statusFilter === f }"
        @click="statusFilter = f"
      >
        {{ f.charAt(0).toUpperCase() + f.slice(1) }}
      </button>
    </div>

    <p class="text-sm mb-4" style="color: var(--text-dim)">
      {{ displayedJobs.length }} of {{ data?.count ?? 0 }} jobs shown
    </p>

    <div class="space-y-4">
      <div
        v-for="job in displayedJobs"
        :key="job.url"
        class="border rounded-lg p-4 shadow-sm"
        :class="{
          '!bg-[var(--surface)]': viewedJobs.has(job.url),
          '!bg-green-50 dark:!bg-green-900': appliedJobs.has(job.url),
          'opacity-60 !bg-gray-200 dark:!bg-gray-800': rejectedJobs.has(job.url),
        }"
        style="background: var(--surface); border-color: var(--border)"
      >
        <h3 class="text-xl font-semibold mb-2">
          <a
            :href="job.url"
            target="_blank"
            rel="noopener"
            class="hover:underline"
            style="color: var(--accent)"
            :class="{ 'line-through': rejectedJobs.has(job.url) }"
            @click.prevent="viewJob(job)"
            >{{ job.title }}</a
          >
        </h3>
        <div class="flex flex-wrap gap-3 text-sm mb-2" style="color: var(--text-dim)">
          <span>{{ job.company }}</span>
          <span>{{ job.location }}</span>
          <span class="px-2 py-0.5 rounded text-xs" style="background: var(--tag-bg); color: var(--tag-text)">{{ job.source }}</span>
          <span v-if="job.date_posted">{{ job.date_posted }}</span>
        </div>
        <div
          class="mb-3 description-content"
          style="color: var(--text-dim)"
          :class="{ 'line-through': rejectedJobs.has(job.url) }"
          v-html="renderDescription(job.description)"
        />
        <div class="flex gap-2 mt-2">
          <button
            type="button"
            @click.stop.prevent="applyToJob(job)"
            class="px-3 py-1.5 rounded text-center no-underline text-white disabled:cursor-not-allowed disabled:opacity-60"
            :class="{ '!bg-green-700': appliedJobs.has(job.url) }"
            style="background: #22c55e"
            :disabled="appliedJobs.has(job.url)"
          >
            {{ appliedJobs.has(job.url) ? "Applied" : "Apply" }}
          </button>
          <button
            class="px-3 py-1.5 rounded text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
            style="background: #ef4444"
            @click="rejectJob(job)"
            :disabled="rejectedJobs.has(job.url)"
          >
            Reject
          </button>
        </div>
      </div>

      <div v-if="displayedJobs.length === 0" class="text-center py-8" style="color: var(--text-dim)">
        No jobs found. Try syncing or adjusting your search.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import MarkdownIt from "markdown-it";

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

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
});

const search = ref("");
const source = ref("");
const syncing = ref(false);
const statusFilter = ref("all");

const viewedJobs = ref<Set<string>>(new Set());
const rejectedJobs = ref<Set<string>>(new Set());
const appliedJobs = ref<Set<string>>(new Set());

onMounted(() => {
  if (!import.meta.client) return;
  const storedViewed = localStorage.getItem("viewedJobs");
  if (storedViewed) viewedJobs.value = new Set(JSON.parse(storedViewed));

  const storedRejected = localStorage.getItem("rejectedJobs");
  if (storedRejected) rejectedJobs.value = new Set(JSON.parse(storedRejected));

  const storedApplied = localStorage.getItem("appliedJobs");
  if (storedApplied) appliedJobs.value = new Set(JSON.parse(storedApplied));
});

const { data, refresh } = await useFetch<JobsResponse>("/api/jobs", {
  query: { q: search, source },
});

watch(search, () => {
  debouncedRefresh();
});

const displayedJobs = computed(() => {
  if (!data.value?.jobs) return [];

  let jobsToDisplay;

  if (statusFilter.value === "new") {
    jobsToDisplay = data.value.jobs.filter(
      (job) =>
        !viewedJobs.value.has(job.url) &&
        !rejectedJobs.value.has(job.url) &&
        !appliedJobs.value.has(job.url),
    );
  } else if (statusFilter.value === "viewed") {
    jobsToDisplay = data.value.jobs.filter(
      (job) => viewedJobs.value.has(job.url) && !appliedJobs.value.has(job.url),
    );
  } else if (statusFilter.value === "applied") {
    jobsToDisplay = data.value.jobs.filter((job) =>
      appliedJobs.value.has(job.url),
    );
  } else if (statusFilter.value === "rejected") {
    jobsToDisplay = data.value.jobs.filter((job) =>
      rejectedJobs.value.has(job.url),
    );
  } else {
    jobsToDisplay = data.value.jobs;
  }

  return [...jobsToDisplay].sort((a, b) => {
    const score = (job: Job) => {
      if (rejectedJobs.value.has(job.url)) return 3;
      if (appliedJobs.value.has(job.url)) return 2;
      if (viewedJobs.value.has(job.url)) return 1;
      return 0;
    };
    return score(a) - score(b);
  });
});

function viewJob(job: Job) {
  window.open(job.url, "_blank", "noopener");
  if (
    !viewedJobs.value.has(job.url) &&
    !rejectedJobs.value.has(job.url) &&
    !appliedJobs.value.has(job.url)
  ) {
    viewedJobs.value.add(job.url);
    localStorage.setItem(
      "viewedJobs",
      JSON.stringify(Array.from(viewedJobs.value)),
    );
  }
}

function applyToJob(job: Job) {
  if (!appliedJobs.value.has(job.url)) {
    appliedJobs.value.add(job.url);
    localStorage.setItem(
      "appliedJobs",
      JSON.stringify(Array.from(appliedJobs.value)),
    );

    if (viewedJobs.value.has(job.url)) {
      viewedJobs.value.delete(job.url);
      localStorage.setItem(
        "viewedJobs",
        JSON.stringify(Array.from(viewedJobs.value)),
      );
    }
  }
}

function rejectJob(job: Job) {
  if (!rejectedJobs.value.has(job.url)) {
    rejectedJobs.value.add(job.url);
    localStorage.setItem(
      "rejectedJobs",
      JSON.stringify(Array.from(rejectedJobs.value)),
    );

    if (viewedJobs.value.has(job.url)) {
      viewedJobs.value.delete(job.url);
      localStorage.setItem(
        "viewedJobs",
        JSON.stringify(Array.from(viewedJobs.value)),
      );
    }
  }
}

function quickSearch(term: string) {
  search.value = term;
  sync();
}

let debounceTimer: ReturnType<typeof setTimeout>;
function debouncedRefresh() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => refresh(), 300);
}

async function sync() {
  syncing.value = true;
  try {
    await $fetch("/api/sync", {
      method: "POST",
      query: { q: search.value },
    });

    const startTime = Date.now();
    const pollInterval = 1000;
    const timeout = 60000;

    while (Date.now() - startTime < timeout) {
      await new Promise(r => setTimeout(r, pollInterval));
      
      const status = await $fetch<{ last_sync: string | null }>("/api/sync/status");
      if (status.last_sync) {
        const syncTime = new Date(status.last_sync).getTime();
        if (syncTime >= startTime) {
          break;
        }
      }
    }

    await refresh();
    cleanupLocalStorage();
  } catch {
    // ignore
  } finally {
    syncing.value = false;
  }
}

function cleanupLocalStorage() {
  if (!data.value?.jobs) return;
  
  const currentUrls = new Set(data.value.jobs.map(j => j.url));
  
  const appliedToRemove = [...appliedJobs.value].filter(url => !currentUrls.has(url));
  if (appliedToRemove.length > 0) {
    const history = JSON.parse(localStorage.getItem("appliedHistory") || "[]");
    history.push(...appliedToRemove.map(url => ({ url, removedAt: new Date().toISOString() })));
    localStorage.setItem("appliedHistory", JSON.stringify(history.slice(-100)));
  }
  
  for (const url of appliedToRemove) {
    appliedJobs.value.delete(url);
  }
  if (appliedToRemove.length > 0) {
    localStorage.setItem("appliedJobs", JSON.stringify([...appliedJobs.value]));
  }
  
  for (const url of [...rejectedJobs.value]) {
    if (!currentUrls.has(url)) {
      rejectedJobs.value.delete(url);
      localStorage.setItem("rejectedJobs", JSON.stringify([...rejectedJobs.value]));
    }
  }
  
  for (const url of [...viewedJobs.value]) {
    if (!currentUrls.has(url)) {
      viewedJobs.value.delete(url);
      localStorage.setItem("viewedJobs", JSON.stringify([...viewedJobs.value]));
    }
  }
}

function renderDescription(description: string) {
  if (!description) return "";
  return markdown.render(description);
}
</script>

<style scoped>
.description-content :deep(p) {
  margin: 0 0 0.5rem;
}

.description-content :deep(p:last-child) {
  margin-bottom: 0;
}

.description-content :deep(ul) {
  list-style: disc;
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}

.description-content :deep(li) {
  margin: 0.2rem 0;
}

.description-content :deep(strong) {
  color: var(--text);
  font-weight: 600;
}

.description-content :deep(a) {
  color: var(--accent);
  text-decoration: underline;
}
</style>
