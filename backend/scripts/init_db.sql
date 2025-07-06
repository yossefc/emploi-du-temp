-- =============================================================================
-- Database Initialization Script for School Timetable Generator
-- This script creates all necessary tables, indexes, and constraints
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- ENUMS AND TYPES
-- =============================================================================

-- User roles
CREATE TYPE user_role AS ENUM ('ADMIN', 'PRINCIPAL', 'TEACHER', 'COORDINATOR');

-- Subject types
CREATE TYPE subject_type AS ENUM ('ACADEMIC', 'SCIENCE_LAB', 'LANGUAGE', 'SPORTS', 'ART', 'MUSIC', 'RELIGION', 'TECHNICAL');

-- Class types
CREATE TYPE class_type AS ENUM ('REGULAR', 'ADVANCED', 'SPECIAL_NEEDS', 'GIFTED');

-- Grade levels
CREATE TYPE grade AS ENUM ('CP', 'CE1', 'CE2', 'CM1', 'CM2', 'SIXIEME', 'CINQUIEME', 'QUATRIEME', 'TROISIEME', 'SECONDE', 'PREMIERE', 'TERMINALE');

-- Room types
CREATE TYPE room_type AS ENUM ('CLASSROOM', 'LAB', 'COMPUTER_ROOM', 'GYM', 'LIBRARY', 'AUDITORIUM', 'MUSIC_ROOM', 'ART_ROOM');

-- Constraint types
CREATE TYPE constraint_type AS ENUM ('TEACHER_AVAILABILITY', 'ROOM_AVAILABILITY', 'CLASS_REQUIREMENT', 'SUBJECT_REQUIREMENT');

-- Days of the week
CREATE TYPE day_of_week AS ENUM ('SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY');

-- =============================================================================
-- USERS TABLE
-- =============================================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'TEACHER',
    is_active BOOLEAN NOT NULL DEFAULT true,
    language_preference VARCHAR(5) NOT NULL DEFAULT 'he',
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SUBJECTS TABLE
-- =============================================================================

CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name_he VARCHAR(255) NOT NULL,
    name_fr VARCHAR(255) NOT NULL,
    subject_type subject_type NOT NULL,
    color_hex VARCHAR(7) NOT NULL DEFAULT '#3366CC',
    abbreviation VARCHAR(10),
    requires_lab BOOLEAN NOT NULL DEFAULT false,
    requires_special_room BOOLEAN NOT NULL DEFAULT false,
    max_hours_per_day INTEGER DEFAULT 2,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_color_hex CHECK (color_hex ~ '^#[0-9A-Fa-f]{6}$'),
    CONSTRAINT valid_max_hours CHECK (max_hours_per_day > 0 AND max_hours_per_day <= 10)
);

-- =============================================================================
-- TEACHERS TABLE
-- =============================================================================

CREATE TABLE teachers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    max_hours_per_week INTEGER NOT NULL DEFAULT 30,
    max_hours_per_day INTEGER NOT NULL DEFAULT 8,
    prefers_consecutive_hours BOOLEAN NOT NULL DEFAULT true,
    is_active BOOLEAN NOT NULL DEFAULT true,
    primary_language VARCHAR(5) NOT NULL DEFAULT 'he',
    can_teach_in_french BOOLEAN NOT NULL DEFAULT false,
    can_teach_in_hebrew BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_hours_per_week CHECK (max_hours_per_week > 0 AND max_hours_per_week <= 60),
    CONSTRAINT valid_hours_per_day CHECK (max_hours_per_day > 0 AND max_hours_per_day <= 12),
    CONSTRAINT language_capability CHECK (can_teach_in_french OR can_teach_in_hebrew)
);

-- =============================================================================
-- TEACHER-SUBJECT ASSOCIATION TABLE
-- =============================================================================

CREATE TABLE teacher_subjects (
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    proficiency_level INTEGER NOT NULL DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (teacher_id, subject_id),
    CONSTRAINT valid_proficiency CHECK (proficiency_level >= 1 AND proficiency_level <= 10)
);

-- =============================================================================
-- ROOMS TABLE
-- =============================================================================

CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name_he VARCHAR(255) NOT NULL,
    name_fr VARCHAR(255) NOT NULL,
    room_type room_type NOT NULL,
    capacity INTEGER NOT NULL,
    floor_number INTEGER,
    building VARCHAR(50),
    has_projector BOOLEAN NOT NULL DEFAULT false,
    has_computer BOOLEAN NOT NULL DEFAULT false,
    has_lab_equipment BOOLEAN NOT NULL DEFAULT false,
    is_accessible BOOLEAN NOT NULL DEFAULT true,
    is_active BOOLEAN NOT NULL DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_capacity CHECK (capacity > 0 AND capacity <= 200)
);

-- =============================================================================
-- CLASS GROUPS TABLE
-- =============================================================================

CREATE TABLE class_groups (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name_he VARCHAR(255) NOT NULL,
    name_fr VARCHAR(255) NOT NULL,
    grade grade NOT NULL,
    class_type class_type NOT NULL DEFAULT 'REGULAR',
    student_count INTEGER NOT NULL,
    max_capacity INTEGER NOT NULL,
    primary_language VARCHAR(5) NOT NULL DEFAULT 'he',
    is_active BOOLEAN NOT NULL DEFAULT true,
    academic_year VARCHAR(9) NOT NULL, -- e.g., "2024-2025"
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_student_count CHECK (student_count > 0 AND student_count <= max_capacity),
    CONSTRAINT valid_max_capacity CHECK (max_capacity > 0 AND max_capacity <= 50),
    CONSTRAINT valid_academic_year CHECK (academic_year ~ '^\d{4}-\d{4}$')
);

-- =============================================================================
-- CLASS SUBJECT REQUIREMENTS TABLE
-- =============================================================================

CREATE TABLE class_subject_requirements (
    id SERIAL PRIMARY KEY,
    class_group_id INTEGER NOT NULL REFERENCES class_groups(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    hours_per_week INTEGER NOT NULL,
    preferred_periods TEXT, -- JSON array of preferred time slots
    avoid_periods TEXT, -- JSON array of periods to avoid
    requires_double_period BOOLEAN NOT NULL DEFAULT false,
    max_consecutive_hours INTEGER DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(class_group_id, subject_id),
    CONSTRAINT valid_hours_per_week CHECK (hours_per_week > 0 AND hours_per_week <= 20),
    CONSTRAINT valid_consecutive_hours CHECK (max_consecutive_hours > 0 AND max_consecutive_hours <= 6)
);

-- =============================================================================
-- TEACHER AVAILABILITY TABLE
-- =============================================================================

CREATE TABLE teacher_availability (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    day_of_week day_of_week NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

-- =============================================================================
-- SCHEDULES TABLE
-- =============================================================================

CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    academic_year VARCHAR(9) NOT NULL,
    semester INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT false,
    is_published BOOLEAN NOT NULL DEFAULT false,
    generated_by INTEGER REFERENCES users(id),
    generation_time TIMESTAMP WITH TIME ZONE,
    solver_stats JSONB, -- Statistics from the constraint solver
    conflicts JSONB, -- Any conflicts or warnings
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_semester CHECK (semester IN (1, 2)),
    CONSTRAINT valid_academic_year CHECK (academic_year ~ '^\d{4}-\d{4}$')
);

-- =============================================================================
-- SCHEDULE ENTRIES TABLE
-- =============================================================================

CREATE TABLE schedule_entries (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    class_group_id INTEGER NOT NULL REFERENCES class_groups(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    day_of_week day_of_week NOT NULL,
    period INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 45,
    is_locked BOOLEAN NOT NULL DEFAULT false, -- Manually locked entries cannot be changed by solver
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_period CHECK (period >= 1 AND period <= 10),
    CONSTRAINT valid_duration CHECK (duration_minutes > 0 AND duration_minutes <= 180),
    UNIQUE(schedule_id, class_group_id, day_of_week, period),
    UNIQUE(schedule_id, teacher_id, day_of_week, period),
    UNIQUE(schedule_id, room_id, day_of_week, period)
);

-- =============================================================================
-- CONSTRAINTS TABLE (for custom scheduling constraints)
-- =============================================================================

CREATE TABLE constraints (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    constraint_type constraint_type NOT NULL,
    target_type VARCHAR(50) NOT NULL, -- 'teacher', 'room', 'class', 'subject'
    target_id INTEGER NOT NULL,
    constraint_data JSONB NOT NULL, -- Flexible constraint definition
    priority INTEGER NOT NULL DEFAULT 5, -- 1 (low) to 10 (high)
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_priority CHECK (priority >= 1 AND priority <= 10)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- User indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Subject indexes
CREATE INDEX idx_subjects_code ON subjects(code);
CREATE INDEX idx_subjects_type ON subjects(subject_type);
CREATE INDEX idx_subjects_active ON subjects(is_active);

-- Teacher indexes
CREATE INDEX idx_teachers_code ON teachers(code);
CREATE INDEX idx_teachers_email ON teachers(email);
CREATE INDEX idx_teachers_active ON teachers(is_active);
CREATE INDEX idx_teachers_language ON teachers(primary_language);

-- Teacher-subject indexes
CREATE INDEX idx_teacher_subjects_teacher ON teacher_subjects(teacher_id);
CREATE INDEX idx_teacher_subjects_subject ON teacher_subjects(subject_id);

-- Room indexes
CREATE INDEX idx_rooms_code ON rooms(code);
CREATE INDEX idx_rooms_type ON rooms(room_type);
CREATE INDEX idx_rooms_active ON rooms(is_active);
CREATE INDEX idx_rooms_capacity ON rooms(capacity);

-- Class group indexes
CREATE INDEX idx_class_groups_code ON class_groups(code);
CREATE INDEX idx_class_groups_grade ON class_groups(grade);
CREATE INDEX idx_class_groups_year ON class_groups(academic_year);
CREATE INDEX idx_class_groups_active ON class_groups(is_active);

-- Class subject requirements indexes
CREATE INDEX idx_class_subject_req_class ON class_subject_requirements(class_group_id);
CREATE INDEX idx_class_subject_req_subject ON class_subject_requirements(subject_id);

-- Teacher availability indexes
CREATE INDEX idx_teacher_availability_teacher ON teacher_availability(teacher_id);
CREATE INDEX idx_teacher_availability_day ON teacher_availability(day_of_week);

-- Schedule indexes
CREATE INDEX idx_schedules_year ON schedules(academic_year);
CREATE INDEX idx_schedules_active ON schedules(is_active);
CREATE INDEX idx_schedules_published ON schedules(is_published);

-- Schedule entries indexes
CREATE INDEX idx_schedule_entries_schedule ON schedule_entries(schedule_id);
CREATE INDEX idx_schedule_entries_class ON schedule_entries(class_group_id);
CREATE INDEX idx_schedule_entries_teacher ON schedule_entries(teacher_id);
CREATE INDEX idx_schedule_entries_room ON schedule_entries(room_id);
CREATE INDEX idx_schedule_entries_day_period ON schedule_entries(day_of_week, period);

-- Constraint indexes
CREATE INDEX idx_constraints_type ON constraints(constraint_type);
CREATE INDEX idx_constraints_target ON constraints(target_type, target_id);
CREATE INDEX idx_constraints_active ON constraints(is_active);

-- =============================================================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON subjects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_teachers_updated_at BEFORE UPDATE ON teachers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_class_groups_updated_at BEFORE UPDATE ON class_groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_class_subject_requirements_updated_at BEFORE UPDATE ON class_subject_requirements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_teacher_availability_updated_at BEFORE UPDATE ON teacher_availability FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_schedule_entries_updated_at BEFORE UPDATE ON schedule_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_constraints_updated_at BEFORE UPDATE ON constraints FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Teacher with subjects view
CREATE VIEW teacher_with_subjects AS
SELECT 
    t.*,
    COALESCE(
        json_agg(
            json_build_object(
                'id', s.id,
                'code', s.code,
                'name_he', s.name_he,
                'name_fr', s.name_fr,
                'subject_type', s.subject_type,
                'proficiency_level', ts.proficiency_level
            )
        ) FILTER (WHERE s.id IS NOT NULL),
        '[]'
    ) as subjects
FROM teachers t
LEFT JOIN teacher_subjects ts ON t.id = ts.teacher_id
LEFT JOIN subjects s ON ts.subject_id = s.id
GROUP BY t.id;

-- Complete schedule view
CREATE VIEW complete_schedule AS
SELECT 
    se.*,
    s.name as schedule_name,
    s.academic_year,
    s.semester,
    cg.code as class_code,
    cg.name_he as class_name_he,
    cg.name_fr as class_name_fr,
    subj.code as subject_code,
    subj.name_he as subject_name_he,
    subj.name_fr as subject_name_fr,
    t.code as teacher_code,
    t.first_name as teacher_first_name,
    t.last_name as teacher_last_name,
    r.code as room_code,
    r.name_he as room_name_he,
    r.name_fr as room_name_fr
FROM schedule_entries se
JOIN schedules s ON se.schedule_id = s.id
JOIN class_groups cg ON se.class_group_id = cg.id
JOIN subjects subj ON se.subject_id = subj.id
JOIN teachers t ON se.teacher_id = t.id
JOIN rooms r ON se.room_id = r.id;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE users IS 'System users including admins, teachers, and coordinators';
COMMENT ON TABLE subjects IS 'Academic subjects taught in the school';
COMMENT ON TABLE teachers IS 'Teaching staff with their capabilities and constraints';
COMMENT ON TABLE teacher_subjects IS 'Many-to-many relationship between teachers and subjects they can teach';
COMMENT ON TABLE rooms IS 'Physical spaces where classes can be held';
COMMENT ON TABLE class_groups IS 'Student groups/classes organized by grade and specialization';
COMMENT ON TABLE class_subject_requirements IS 'Required hours per subject for each class';
COMMENT ON TABLE teacher_availability IS 'Time slots when teachers are available to teach';
COMMENT ON TABLE schedules IS 'Generated timetable versions';
COMMENT ON TABLE schedule_entries IS 'Individual time slots in a timetable';
COMMENT ON TABLE constraints IS 'Custom scheduling constraints and preferences';

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

INSERT INTO users (username, email, hashed_password, full_name, role, language_preference) 
VALUES ('setup', 'setup@temp.com', 'temp', 'Setup Complete', 'ADMIN', 'he'); 