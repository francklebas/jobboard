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
      <div class="search-group">
        <input
          v-model="search"
          type="text"
          placeholder="Search jobs (React, Vue, TypeScript...)"
          @keyup.enter="sync"
        />
        <button class="btn" :disabled="syncing" @click="sync">
          {{ syncing ? "Searching..." : "Search" }}
        </button>
      </div>

      <select v-model="source" @change="refresh()">
        <option value="">All sources</option>
        <option value="indeed">Indeed</option>
        <option value="linkedin">LinkedIn</option>
      </select>

      <button class="btn-sync" :disabled="syncing" @click="sync">
        {{ syncing ? "Syncing..." : "Sync Now" }}
      </button>
    </div>

    <div class="shortcuts">
      <span>Quick Search:</span>
      <button @click="quickSearch('React developer')">React</button>
      <button @click="quickSearch('Vue developer')">Vue</button>
      <button @click="quickSearch('TypeScript developer')">TypeScript</button>
      <button @click="quickSearch('Frontend developer')">Frontend</button>
    </div>

    <div class="filters">
      <span>Filter by:</span>
      <button @click="statusFilter = 'all'" :class="{ active: statusFilter === 'all' }">All</button>
      <button @click="statusFilter = 'new'" :class="{ active: statusFilter === 'new' }">New</button>
      <button @click="statusFilter = 'viewed'" :class="{ active: statusFilter === 'viewed' }">Viewed</button>
      <button @click="statusFilter = 'applied'" :class="{ active: statusFilter === 'applied' }">Applied</button>
      <button @click="statusFilter = 'rejected'" :class="{ active: statusFilter === 'rejected' }">Rejected</button>
    </div>

    <p class="count">{{ displayedJobs.length }} of {{ data?.count ?? 0 }} jobs shown</p>

    <div class="job-list">
      <div
        v-for="job in displayedJobs"
        :key="job.url"
        class="job-card"
        :class="{
          viewed: viewedJobs.has(job.url),
          applied: appliedJobs.has(job.url),
          rejected: rejectedJobs.has(job.url),
        }"
      >
        <h3>
          <a
            :href="job.url"
            target="_blank"
            rel="noopener"
            @click.prevent="viewJob(job)"
            >{{ job.title }}</a
          >
        </h3>
        <div class="job-meta">
          <span>{{ job.company }}</span>
          <span>{{ job.location }}</span>
          <span class="tag">{{ job.source }}</span>
          <span v-if="job.date_posted">{{ job.date_posted }}</span>
        </div>
        <p class="job-desc">{{ job.description }}</p>
        <div class="job-actions">
           <a :href="job.url" target="_blank" rel="noopener" @click="applyToJob(job)" class="btn-apply">
            {{ appliedJobs.has(job.url) ? 'Applied' : 'Apply' }}
          </a>
          <button
            class="btn-reject"
            @click="rejectJob(job)"
            :disabled="rejectedJobs.has(job.url)"
          >
            Reject
          </button>
        </div>
      </div>

      <div v-if="displayedJobs.length === 0" class="empty">
        No jobs found. Try syncing or adjusting your search.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';

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
const statusFilter = ref('all'); // 'all', 'new', 'viewed', 'applied', 'rejected'

const viewedJobs = ref<Set<string>>(new Set());
const rejectedJobs = ref<Set<string>>(new Set());
const appliedJobs = ref<Set<string>>(new Set());

onMounted(() => {
  const storedViewed = localStorage.getItem('viewedJobs');
  if (storedViewed) viewedJobs.value = new Set(JSON.parse(storedViewed));

  const storedRejected = localStorage.getItem('rejectedJobs');
  if (storedRejected) rejectedJobs.value = new Set(JSON.parse(storedRejected));

  const storedApplied = localStorage.getItem('appliedJobs');
  if (storedApplied) appliedJobs.value = new Set(JSON.parse(storedApplied));
});

const { data, refresh } = await useFetch<JobsResponse>("/api/jobs", {
  query: { q: search, source },
});

// Watch search changes to trigger local filtering
watch(search, () => {
  debouncedRefresh();
});

const displayedJobs = computed(() => {
  if (!data.value?.jobs) return [];

  let jobsToDisplay;

  if (statusFilter.value === 'new') {
    jobsToDisplay = data.value.jobs.filter(job => !viewedJobs.value.has(job.url) && !rejectedJobs.value.has(job.url) && !appliedJobs.value.has(job.url));
  } else if (statusFilter.value === 'viewed') {
    jobsToDisplay = data.value.jobs.filter(job => viewedJobs.value.has(job.url) && !appliedJobs.value.has(job.url));
  } else if (statusFilter.value === 'applied') {
    jobsToDisplay = data.value.jobs.filter(job => appliedJobs.value.has(job.url));
  } else if (statusFilter.value === 'rejected') {
    jobsToDisplay = data.value.jobs.filter(job => rejectedJobs.value.has(job.url));
  } else { // 'all'
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
  window.open(job.url, '_blank', 'noopener');
  if (!viewedJobs.value.has(job.url) && !rejectedJobs.value.has(job.url) && !appliedJobs.value.has(job.url)) {
    viewedJobs.value.add(job.url);
    localStorage.setItem('viewedJobs', JSON.stringify(Array.from(viewedJobs.value)));
  }
}

function applyToJob(job: Job) {
  if (!appliedJobs.value.has(job.url)) {
    appliedJobs.value.add(job.url);
    localStorage.setItem('appliedJobs', JSON.stringify(Array.from(appliedJobs.value)));

    if (viewedJobs.value.has(job.url)) {
      viewedJobs.value.delete(job.url);
      localStorage.setItem('viewedJobs', JSON.stringify(Array.from(viewedJobs.value)));
    }
  }
}

function rejectJob(job: Job) {
  if (!rejectedJobs.value.has(job.url)) {
    rejectedJobs.value.add(job.url);
    localStorage.setItem('rejectedJobs', JSON.stringify(Array.from(rejectedJobs.value)));

    if (viewedJobs.value.has(job.url)) {
        viewedJobs.value.delete(job.url)
        localStorage.setItem('viewedJobs', JSON.stringify(Array.from(viewedJobs.value)));
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
    // Send the current search term to the backend for scraping
    await $fetch("/api/sync", {
      method: "POST",
      query: { q: search.value }
    });

    // Wait a bit for scrape to start/finish, then refresh
    // Note: In a real app, we might want to poll for status or use websockets
    setTimeout(async () => {
      await refresh();
      syncing.value = false;
    }, 5000); // Increased timeout slightly as scraping might take time
  } catch {
    syncing.value = false;
  }
}
</script>

<style>
.job-card.viewed {
  background-color: #f9f9f9;
}
.job-card.applied {
  background-color: #e8f5e9; /* Light green */
}
.job-card.rejected {
  opacity: 0.6;
  background-color: #f0f0f0;
}
.job-card.rejected h3 a, .job-card.rejected .job-desc {
  text-decoration: line-through;
}
.job-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}
.btn-reject, .btn-apply {
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}
.btn-apply {
  background: #28a745; /* Green */
}
.btn-reject {
  background: #dc3545; /* Red */
}
.btn-reject:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.controls {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
}
.search-group {
  display: flex;
  gap: 10px;
}
.shortcuts {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.shortcuts button {
  background: #e0e0e0;
  border: none;
  padding: 4px 8px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.9em;
}
.shortcuts button:hover {
  background: #d0d0d0;
}
.filters {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 25px;
  flex-wrap: wrap;
}
.filters button {
  background: #f0f0f0;
  border: 1px solid #ccc;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}
.filters button.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}
.btn-sync {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}
.btn-sync:hover {
  background-color: #5a6268;
}
.btn-sync:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
