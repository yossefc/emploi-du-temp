/**
 * Types miroir du backend (app/schemas/).
 * Pas de génération auto pour MVP — on écrit à la main.
 * À synchroniser quand on touche aux schemas Pydantic.
 */

// ---- Enums ----

export const GroupingPolicy = {
  CLASS_CENTRIC: "class_centric",
  GROUP_CENTRIC: "group_centric",
} as const;
export type GroupingPolicy = (typeof GroupingPolicy)[keyof typeof GroupingPolicy];

export const GroupType = {
  WHOLE_CLASS: "whole_class",
  LEVEL_GROUP: "level_group",
  OPTION_GROUP: "option_group",
  GENDER_GROUP: "gender_group",
  SPLIT_GROUP: "split_group",
} as const;
export type GroupType = (typeof GroupType)[keyof typeof GroupType];

export const ScheduleStatus = {
  DRAFT: "draft",
  ACTIVE: "active",
  ARCHIVED: "archived",
} as const;
export type ScheduleStatus = (typeof ScheduleStatus)[keyof typeof ScheduleStatus];

export const ConstraintPriority = {
  HARD: "hard",
  SOFT: "soft",
} as const;
export type ConstraintPriority = (typeof ConstraintPriority)[keyof typeof ConstraintPriority];

export const ConstraintOriginRole = {
  SYSTEM: "system",
  SCHOOL_ADMIN: "school_admin",
  TEACHER: "teacher",
  AI_PARSED: "ai_parsed",
} as const;
export type ConstraintOriginRole =
  (typeof ConstraintOriginRole)[keyof typeof ConstraintOriginRole];

// Liste de tous les types de contraintes supportés MVP (mirror du registry backend)
export const ConstraintType = {
  BLOCK_SLOT_SCHOOL: "block_slot_school",
  BLOCK_SLOT_CLASS: "block_slot_class",
  BLOCK_SLOT_GROUP: "block_slot_group",
  BLOCK_SLOT_TEACHER: "block_slot_teacher",
  BLOCK_SLOT_ROOM: "block_slot_room",
  SUBJECT_REQUIRED_SLOT_RANGE: "subject_required_slot_range",
  SUBJECT_MAX_PER_DAY: "subject_max_per_day",
  SUBJECT_CONSECUTIVE_HOURS: "subject_consecutive_hours",
  GROUP_HOURS_PER_WEEK: "group_hours_per_week",
  TEACHER_MAX_HOURS_WEEK: "teacher_max_hours_week",
  TEACHER_MAX_HOURS_DAY: "teacher_max_hours_day",
  TEACHER_MAX_CONSECUTIVE: "teacher_max_consecutive",
  TEACHER_QUALIFIED_FOR_SUBJECT: "teacher_qualified_for_subject",
  TEACHER_LANGUAGE_REQUIRED: "teacher_language_required",
  TEACHERS_MUST_TEACH_TOGETHER: "teachers_must_teach_together",
  EXTRA_HOURS_AT_DAY_EDGE: "extra_hours_at_day_edge",
} as const;
export type ConstraintType = (typeof ConstraintType)[keyof typeof ConstraintType];

// ---- Entités ----

export interface School {
  id: number;
  code: string;
  name: string;
  timezone: string;
  default_language: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface SchoolCreate {
  code: string;
  name: string;
  timezone?: string;
  default_language?: string;
  is_active?: boolean;
}

export interface TimeSlot {
  id: number;
  school_id: number;
  day_of_week: number;
  slot_index: number;
  start_time: string; // "HH:MM:SS"
  end_time: string;
  is_break: boolean;
  is_active: boolean;
  label?: string | null;
}

export type TimeSlotInput = Omit<TimeSlot, "id" | "school_id">;

export interface Grade {
  id: number;
  school_id: number;
  code: string;
  name: string;
  order: number;
  grouping_policy: GroupingPolicy;
  created_at: string;
  updated_at?: string | null;
}

export interface SchoolClass {
  id: number;
  school_id: number;
  grade_id: number;
  code: string;
  name: string;
  student_count: number;
  homeroom_teacher_id?: number | null;
  created_at: string;
  updated_at?: string | null;
}

export interface Subject {
  id: number;
  school_id: number;
  code: string;
  name_fr: string;
  name_he: string;
  abbreviation?: string | null;
  color_hex?: string | null;
  required_room_type?: string | null;
  is_religious: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface Teacher {
  id: number;
  school_id: number;
  code: string;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  max_hours_per_week?: number | null;
  max_hours_per_day?: number | null;
  languages: string[];
  is_active: boolean;
  qualified_subject_ids: number[];
  created_at: string;
  updated_at?: string | null;
}

export interface Room {
  id: number;
  school_id: number;
  code: string;
  name: string;
  capacity: number;
  room_type?: string | null;
  building?: string | null;
  floor?: number | null;
  equipment?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface Group {
  id: number;
  school_id: number;
  grade_id: number;
  subject_id: number;
  label: string;
  group_type: GroupType;
  hours_per_week: number;
  student_count?: number | null;
  parallel_cohort_id?: number | null;
  teacher_ids: number[];
  source_class_ids: number[];
  created_at: string;
  updated_at?: string | null;
}

export interface ParallelCohort {
  id: number;
  school_id: number;
  grade_id?: number | null;
  label: string;
  group_ids: number[];
  created_at: string;
  updated_at?: string | null;
}

export interface Constraint {
  id: number;
  school_id: number;
  constraint_type: ConstraintType;
  priority: ConstraintPriority;
  weight?: number | null;
  parameters: Record<string, unknown>;
  is_active: boolean;
  origin_role: ConstraintOriginRole;
  origin_user_id?: number | null;
  origin_description?: string | null;
  origin_raw_text?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface Schedule {
  id: number;
  school_id: number;
  name: string;
  status: ScheduleStatus;
  generated_at?: string | null;
  generator_user_id?: number | null;
  relaxed_constraints_report?: Record<string, unknown> | null;
  quality_score?: Record<string, unknown> | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ScheduleEntry {
  id: number;
  group_id: number;
  room_id?: number | null;
  day_of_week: number;
  slot_index: number;
}

export interface ScheduleWithEntries extends Schedule {
  entries: ScheduleEntry[];
}

// ---- Génération + dialogue conflit ----

export interface GenerateRequest {
  school_id: number;
  name?: string;
  disabled_constraint_ids?: number[];
  max_time_seconds?: number;
}

export interface ConflictSuggestion {
  kind: string;
  title_he: string;
  title_fr: string;
  description_he: string;
  description_fr: string;
  // Si non-null, l'UI peut afficher un bouton "Appliquer"
  auto_action: {
    verb: "patch_constraint" | "patch_group" | "delete_constraint";
    target_id: number;
    patch?: Record<string, unknown>;
  } | null;
}

export interface ConstraintConflictInfo {
  constraint_id: number | null;
  constraint_type: string;
  title_he: string;
  title_fr: string;
  detail_he: string;
  detail_fr: string;
  origin: string;
  suggestions: ConflictSuggestion[];
}

export type GenerateResponse =
  | {
      success: true;
      schedule_id: number;
      placed_entries: number;
      relaxed_constraint_ids: number[];
      solver_time_seconds: number;
    }
  | {
      success: false;
      conflicts: ConstraintConflictInfo[];
      solver_time_seconds: number;
      message: string;
      timeout?: false;
    }
  | {
      success: false;
      timeout: true;
      solver_time_seconds: number;
      message: string;
    };
