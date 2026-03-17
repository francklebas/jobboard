<template>
  <div class="max-w-4xl mx-auto p-6">
    <header class="mb-6">
      <h1 class="text-3xl font-bold mb-2">JobBoard Stockholm</h1>
      <div class="text-sm text-gray-600">
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
          @keyup.enter="sync"
        />
        <button 
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400" 
          :disabled="syncing" 
          @click="sync"
        >
          {{ syncing ? "Searching..." : "Search" }}
        </button>
      </div>

      <select v-model="source" @change="refresh()" class="border rounded px-3 py-2">
        <option value="">All sources</option>
        <option value="indeed">Indeed</option>
        <option value="linkedin">LinkedIn</option>
      </select>

      <button 
        class="bg-gray-600 text-white px-3 py-2 rounded hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed" 
        :disabled="syncing" 
        @click="sync"
      >
        {{ syncing ? "Syncing..." : "Sync Now" }}
      </button>
    </div>

    <div class="flex flex-wrap gap-2 items-center mb-5">
      <span class="text-sm text-gray-600">Quick Search:</span>
      <button 
        v-for="term in ['React developer', 'Vue developer', 'TypeScript developer', 'Frontend developer']"
        :key="term"
        class="bg-gray-200 border-none px-2 py-1 rounded-full text-sm cursor-pointer hover:bg-gray-300"
        @click="quickSearch(term)"
      >
        {{ term.split(' ')[0] }}
      </button>
    </div>

    <div class="flex flex-wrap gap-3 items-center mb-6">
      <span class="text-sm text-gray-600">Filter by:</span>
      <button
        v-for="f in ['all', 'new', 'viewed', 'applied', 'rejected']"
        :key="f"
        class="bg-gray-100 border border-gray-300 px-3 py-2 rounded cursor-pointer hover:bg-gray-200"
        :class="{ 'bg-blue-600 text-white border-blue-600': statusFilter === f }"
        @click="statusFilter = f"
      >
        {{ f.charAt(0).toUpperCase() + f.slice(1) }}
      </button>
    </div>

    <p class="text-sm text-gray-600 mb-4">
      {{ displayedJobs.length }} of {{ data?.count ?? 0 }} jobs shown
    </p>

    <div class="space-y-4">
      <div
        v-for="job in displayedJobs"
        :key="job.url"
        class="border rounded-lg p-4 shadow-sm"
        :class="{
          'bg-gray-100': viewedJobs.has(job.url),
          'bg-green-50': appliedJobs.has(job.url),
          'opacity-60 bg-gray-200': rejectedJobs.has(job.url),
        }"
      >
        <h3 class="text-xl font-semibold mb-2">
          <a
            :href="job.url"
            target="_blank"
            rel="noopener"
            class="text-blue-600 hover:underline"
            :class="{ 'line-through': rejectedJobs.has(job.url) }"
            @click.prevent="viewJob(job)"
            >{{ job.title }}</a
          >
        </h3>
        <div class="flex flex-wrap gap-3 text-sm text-gray-600 mb-2">
          <span>{{ job.company }}</span>
          <span>{{ job.location }}</span>
          <span class="bg-gray-200 px-2 py-0.5 rounded text-xs">{{ job.source }}</span>
          <span v-if="job.date_posted">{{ job.date_posted }}</span>
        </div>
        <p class="text-gray-700 mb-3" :class="{ 'line-through': rejectedJobs.has(job.url) }">
          {{ job.description }}
        </p>
        <div class="flex gap-2 mt-2">
          <a
            :href="job.url"
            target="_blank"
            rel="noopener"
            @click="applyToJob(job)"
            class="bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 text-center no-underline"
          >
            {{ appliedJobs.has(job.url) ? "Applied" : "Apply" }}
          </a>
          <button
            class="bg-red-600 text-white px-3 py-1.5 rounded hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            @click="rejectJob(job)"
            :disabled="rejectedJobs.has(job.url)"
          >
            Reject
          </button>
        </div>
      </div>

      <div v-if="displayedJobs.length === 0" class="text-center py-8 text-gray-500">
        No jobs found. Try syncing or adjusting your search.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";

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
    const syncResponse = await $fetch<{ started_at: number }>("/api/sync", {
      method: "POST",
      query: { q: search.value },
    });

    const startTime = syncResponse.started_at;
    const pollInterval = 1000;
    const timeout = 60000;

    while (Date.now() / 1000 - startTime < timeout) {
      await new Promise(r => setTimeout(r, pollInterval));
      
      const status = await $fetch<{ last_sync: string | null }>("/api/sync/status");
      if (status.last_sync) {
        const syncTime = new Date(status.last_sync).getTime() / 1000;
        if (syncTime >= startTime) {
          break;
        }
      }
    }

    await refresh();
  } catch {
    // ignore
  } finally {
    syncing.value = false;
  }
}
</script>
