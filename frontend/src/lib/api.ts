/**
 * Client API typé — wrapper léger autour de fetch.
 * Vite proxy /api → backend localhost:8004 (cf. vite.config.ts).
 */

import type {
  Constraint,
  GenerateRequest,
  GenerateResponse,
  Grade,
  Group,
  ParallelCohort,
  Room,
  Schedule,
  ScheduleWithEntries,
  School,
  SchoolClass,
  Subject,
  Teacher,
  TimeSlot,
  TimeSlotInput,
} from "./types";

const BASE = "/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string, public body?: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...init,
  });
  if (res.status === 204) return undefined as T;
  const json = await res.json().catch(() => undefined);
  if (!res.ok) {
    const message =
      (json && typeof json === "object" && "detail" in json && String(json.detail)) ||
      res.statusText;
    throw new ApiError(res.status, message, json);
  }
  return json as T;
}

export const api = {
  // ---- Schools ----
  schools: {
    list: () => request<School[]>("GET", "/schools"),
    get: (id: number) => request<School>("GET", `/schools/${id}`),
    create: (data: { code: string; name: string; default_language?: string }) =>
      request<School>("POST", "/schools", data),
    update: (id: number, patch: Partial<School>) =>
      request<School>("PATCH", `/schools/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/schools/${id}`),
    // Grille horaire
    getTimeGrid: (id: number) => request<TimeSlot[]>("GET", `/schools/${id}/time-grid`),
    setTimeGrid: (id: number, slots: TimeSlotInput[]) =>
      request<TimeSlot[]>("POST", `/schools/${id}/time-grid`, { slots }),
  },

  // ---- Grades ----
  grades: {
    list: (schoolId: number) => request<Grade[]>("GET", `/grades?school_id=${schoolId}`),
    get: (id: number) => request<Grade>("GET", `/grades/${id}`),
    create: (data: Omit<Grade, "id" | "created_at" | "updated_at">) =>
      request<Grade>("POST", "/grades", data),
    update: (id: number, patch: Partial<Grade>) =>
      request<Grade>("PATCH", `/grades/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/grades/${id}`),
  },

  // ---- Classes ----
  classes: {
    list: (schoolId: number) =>
      request<SchoolClass[]>("GET", `/classes?school_id=${schoolId}`),
    get: (id: number) => request<SchoolClass>("GET", `/classes/${id}`),
    create: (data: Omit<SchoolClass, "id" | "created_at" | "updated_at">) =>
      request<SchoolClass>("POST", "/classes", data),
    update: (id: number, patch: Partial<SchoolClass>) =>
      request<SchoolClass>("PATCH", `/classes/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/classes/${id}`),
  },

  // ---- Subjects ----
  subjects: {
    list: (schoolId: number) =>
      request<Subject[]>("GET", `/subjects?school_id=${schoolId}`),
    get: (id: number) => request<Subject>("GET", `/subjects/${id}`),
    create: (data: Omit<Subject, "id" | "created_at" | "updated_at">) =>
      request<Subject>("POST", "/subjects", data),
    update: (id: number, patch: Partial<Subject>) =>
      request<Subject>("PATCH", `/subjects/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/subjects/${id}`),
  },

  // ---- Teachers ----
  teachers: {
    list: (schoolId: number) =>
      request<Teacher[]>("GET", `/teachers?school_id=${schoolId}`),
    get: (id: number) => request<Teacher>("GET", `/teachers/${id}`),
    create: (
      data: Omit<Teacher, "id" | "created_at" | "updated_at">
    ) => request<Teacher>("POST", "/teachers", data),
    update: (id: number, patch: Partial<Teacher>) =>
      request<Teacher>("PATCH", `/teachers/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/teachers/${id}`),
  },

  // ---- Rooms ----
  rooms: {
    list: (schoolId: number) => request<Room[]>("GET", `/rooms?school_id=${schoolId}`),
    get: (id: number) => request<Room>("GET", `/rooms/${id}`),
    create: (data: Omit<Room, "id" | "created_at" | "updated_at">) =>
      request<Room>("POST", "/rooms", data),
    update: (id: number, patch: Partial<Room>) =>
      request<Room>("PATCH", `/rooms/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/rooms/${id}`),
  },

  // ---- Groups ----
  groups: {
    list: (schoolId: number, gradeId?: number) => {
      const q = `school_id=${schoolId}${gradeId ? `&grade_id=${gradeId}` : ""}`;
      return request<Group[]>("GET", `/groups?${q}`);
    },
    get: (id: number) => request<Group>("GET", `/groups/${id}`),
    create: (data: Omit<Group, "id" | "created_at" | "updated_at">) =>
      request<Group>("POST", "/groups", data),
    update: (id: number, patch: Partial<Group>) =>
      request<Group>("PATCH", `/groups/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/groups/${id}`),
  },

  // ---- ParallelCohorts ----
  cohorts: {
    list: (schoolId: number) =>
      request<ParallelCohort[]>("GET", `/cohorts?school_id=${schoolId}`),
    get: (id: number) => request<ParallelCohort>("GET", `/cohorts/${id}`),
    create: (
      data: Omit<ParallelCohort, "id" | "group_ids" | "created_at" | "updated_at">
    ) => request<ParallelCohort>("POST", "/cohorts", data),
    update: (id: number, patch: Partial<ParallelCohort>) =>
      request<ParallelCohort>("PATCH", `/cohorts/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/cohorts/${id}`),
  },

  // ---- Constraints ----
  constraints: {
    list: (schoolId: number) =>
      request<Constraint[]>("GET", `/constraints?school_id=${schoolId}`),
    get: (id: number) => request<Constraint>("GET", `/constraints/${id}`),
    create: (data: Omit<Constraint, "id" | "created_at" | "updated_at">) =>
      request<Constraint>("POST", "/constraints", data),
    update: (id: number, patch: Partial<Constraint>) =>
      request<Constraint>("PATCH", `/constraints/${id}`, patch),
    remove: (id: number) => request<void>("DELETE", `/constraints/${id}`),
    typesSchema: () =>
      request<Record<string, { class_name: string; parameters_schema: unknown }>>(
        "GET",
        "/constraints/types/schema"
      ),
  },

  // ---- Schedules / Génération ----
  schedules: {
    list: (schoolId: number) =>
      request<Schedule[]>("GET", `/schedules?school_id=${schoolId}`),
    get: (id: number) =>
      request<ScheduleWithEntries>("GET", `/schedules/${id}`),
    generate: (req: GenerateRequest) =>
      request<GenerateResponse>("POST", "/schedules/generate", req),
    accept: (id: number) =>
      request<Schedule>("POST", `/schedules/${id}/accept`),
    remove: (id: number) => request<void>("DELETE", `/schedules/${id}`),
  },
};

export { ApiError };
