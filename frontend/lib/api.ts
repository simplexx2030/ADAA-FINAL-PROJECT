/**
 * Every call the interface makes to the ADAA backend.
 *
 * Kept in one file on purpose. If you want to know what the interface can
 * ask the server for, this is the whole list, and nothing else in the app
 * calls fetch() directly.
 *
 * The backend is the source of truth for everything shown on screen. This
 * file never calculates a rating, a distance or an availability -- it only
 * asks.
 */

const API =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

/** Something went wrong on the server side, with a readable reason. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
      cache: "no-store",
    });
  } catch {
    // The server is not running, or the browser could not reach it. This is
    // the most common problem during a demonstration, so it gets a message
    // that says what to do rather than "Failed to fetch".
    throw new ApiError(
      `Cannot reach the ADAA backend at ${API}. Is it running? Start it with: ` +
        `backend/.venv/Scripts/python -m uvicorn app.main:app --reload --app-dir backend`,
      0,
    );
  }

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* the body was not JSON; the status line will do */
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

const get = <T,>(path: string) => request<T>(path);
const post = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });

/* ------------------------------------------------------------------ */
/* What the backend returns                                            */
/* ------------------------------------------------------------------ */

export type Worker = {
  id: string;
  name: string;
  location_name: string | null;
  verification_status: string;
  availability_status: string;
  average_rating: number | null;
  completed_jobs: number;
  attendance_rate: number | null;
  reliability_score: number | null;
  experience_years: number;
  preferred_language: string;
  travel_radius_km: number;
  verified_skills?: string | null;
  crew_role?: string | null;
  crew_id?: string | null;
  crew_name?: string | null;
};

export type WorkerProfile = Worker & {
  skills: { name: string; category: string; verification_status: string; years_experience: number }[];
  crew_history: {
    crew_id: string;
    crew_name: string;
    role: string;
    status: string;
    joined_at: string;
    left_at: string | null;
  }[];
  ratings_received: { job_id: string; rating: number; comment: string | null; created_at: string }[];
};

export type Crew = {
  id: string;
  name: string;
  primary_trade: string;
  location_name: string | null;
  availability_status: string;
  rating: number | null;
  completed_jobs: number;
  reliability_score: number | null;
  verification_status: string;
  leader_name: string | null;
  active_members?: number;
  available_members?: number;
};

export type CrewProfile = Crew & {
  members: {
    id: string;
    name: string;
    role: string;
    status: string;
    joined_at: string;
    left_at: string | null;
    worker_own_rating: number | null;
    worker_own_completed_jobs: number;
    availability_status: string;
  }[];
};

export type Candidate = {
  kind: "crew" | "worker";
  id: string;
  name: string;
  supply: number;
  distance_km: number;
  /** 0-100, from the six weighted factors in `scores`. */
  match_score: number;
  scores: {
    skill: number;
    availability: number;
    reliability: number;
    rating: number;
    proximity: number;
    experience: number;
  };
  /** The figures behind the score. Which keys appear depends on kind. */
  evidence: {
    // workers
    average_rating?: number | null;
    completed_jobs?: number;
    attendance_rate?: number | null;
    years_in_skill?: number;
    location?: string;
    // crews
    crew_rating?: number | null;
    crew_completed_jobs?: number;
    qualified_available_members?: number;
    contributing?: number;
    of_available?: number;
    member_names?: string[];
  };
};

export type Match = {
  request: {
    skill: string;
    quantity: number;
    date: string;
    location: string;
    search_radius_km: number;
  };
  filled: number;
  shortfall: number;
  complete: boolean;
  selection: Candidate[];
  weights_used: Record<string, number>;
};

export type ChatReply = {
  reply: string;
  model: string;
  tools_used: { tool: string; arguments: Record<string, unknown> }[];
  grounded: boolean;
  cached: boolean;
  session_id?: string;
};

export type Independence = {
  found: boolean;
  worker_id: string;
  name: string;
  score: number;
  readiness: string;
  recommendation: string;
  blockers: string[];
  factors: Record<string, number>;
  important: string;
  evidence: {
    completed_jobs: number;
    average_rating: number | null;
    attendance_rate: number | null;
    reliability_score: number | null;
    verified_skills: string[];
    distinct_contractors: number;
    contractors: { company: string; jobs: number }[];
    no_shows: number;
  };
};

export type Reputation = {
  worker_id: string;
  completed_jobs: number;
  no_shows: number;
  average_rating: number | null;
  ratings_count: number;
  days_booked: number;
  days_attended: number;
  attendance_rate: number | null;
  reliability_score: number | null;
};

export type NewJob = {
  title: string;
  skill_required: string;
  workers_required: number;
  location: string;
  date: string;
  start_time?: string;
  wage?: number | null;
  site_address?: string;
  description?: string;
  contractor_id?: string;
};

export type Job = {
  id: string;
  title: string;
  skill_required: string;
  workers_required: number;
  location_name: string | null;
  date: string;
  start_time: string;
  wage: number | null;
  status: string;
  contractor_id: string;
};

/* ------------------------------------------------------------------ */
/* The calls                                                           */
/* ------------------------------------------------------------------ */

export const api = {
  health: () => get<{ status: string }>("/health"),
  databaseHealth: () => get<{ status: string; workers: number }>("/health/database"),
  status: () =>
    get<{
      name: string;
      step: string;
      gemini_model: string;
      gemini_key_configured: boolean;
      database_configured: boolean;
    }>("/"),

  workers: (params?: { skill?: string; location?: string }) => {
    const query = new URLSearchParams();
    if (params?.skill) query.set("skill", params.skill);
    if (params?.location) query.set("location", params.location);
    const suffix = query.toString() ? `?${query}` : "";
    return get<{ workers: Worker[] }>(`/api/workers${suffix}`);
  },
  worker: (id: string) => get<WorkerProfile>(`/api/workers/${id}`),
  workerReputation: (id: string) => get<Reputation>(`/api/workers/${id}/reputation`),
  workerIndependence: (id: string) => get<Independence>(`/api/workers/${id}/independence`),

  crews: () => get<{ crews: Crew[] }>("/api/crews"),
  crew: (id: string) => get<CrewProfile>(`/api/crews/${id}`),

  skills: () => get<{ skills: { id: number; name: string; category: string }[] }>("/api/skills"),
  locations: () =>
    get<{ locations: { name: string; lat: number; lng: number; workers: number }[] }>(
      "/api/locations",
    ),

  match: (params: { skill: string; quantity: number; location: string; radius_km?: number }) => {
    const query = new URLSearchParams({
      skill: params.skill,
      quantity: String(params.quantity),
      location: params.location,
    });
    if (params.radius_km) query.set("radius_km", String(params.radius_km));
    return get<Match>(`/api/match/workforce?${query}`);
  },

  chat: (body: {
    message: string;
    history?: { role: string; text: string }[];
    session_id?: string | null;
  }) => post<ChatReply>("/api/agent/chat", body),

  jobs: () => get<{ total: number; jobs: Job[] }>("/api/jobs"),
  createJob: (job: NewJob) => post<{ job_id: string; status: string }>("/api/jobs", job),
  jobRecommendation: (id: string) =>
    get<Match & { job_id: string }>(`/api/jobs/${id}/recommendation`),
  jobOffers: (id: string) =>
    get<{
      job_id: string;
      offers: {
        assignment_id: number;
        who: string;
        status: string;
        assignment_type: string;
      }[];
    }>(`/api/jobs/${id}/offers`),

  action: (id: string) => get<Record<string, unknown>>(`/api/actions/${id}`),
  confirmAction: (id: string) => post<Record<string, unknown>>(`/api/actions/${id}/confirm`),
  cancelAction: (id: string) => post<Record<string, unknown>>(`/api/actions/${id}/cancel`),

  sessions: () =>
    get<{
      sessions: {
        session_id: string;
        started_at: string;
        last_action_at: string;
        actions: number;
        tool_calls: number;
        failures: number;
        tools_used: string[] | null;
      }[];
    }>("/api/agent/sessions"),

  toolUsage: () =>
    get<{
      tools: {
        tool_name: string;
        calls: number;
        failures: number;
        average_ms: number | null;
      }[];
    }>("/api/agent/tool-usage"),
  sessionTrail: (id: string) =>
    get<{
      session_id: string;
      actions: {
        id: number;
        action_type: string;
        tool_name: string | null;
        input: unknown;
        success: boolean;
        duration_ms: number | null;
        created_at: string;
      }[];
    }>(`/api/agent/sessions/${id}`),
};
