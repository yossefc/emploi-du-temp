-- =============================================================================
-- Seed Data for School Timetable Generator
-- This script inserts initial test data including admin user and sample records
-- =============================================================================

-- =============================================================================
-- ADMIN USER
-- =============================================================================

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, full_name, role, language_preference) VALUES
('admin', 'admin@school.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdhXYCAEU8VD4V.', 'Administrateur Principal', 'ADMIN', 'he'),
('principal', 'principal@school.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdhXYCAEU8VD4V.', 'מנהל בית הספר', 'PRINCIPAL', 'he'),
('coordinator', 'coordinator@school.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdhXYCAEU8VD4V.', 'רכז מערכת שעות', 'COORDINATOR', 'he');

-- =============================================================================
-- SUBJECTS
-- =============================================================================

INSERT INTO subjects (code, name_he, name_fr, subject_type, color_hex, abbreviation, requires_lab, requires_special_room, max_hours_per_day) VALUES
-- Core Academic Subjects
('MATH101', 'מתמטיקה', 'Mathématiques', 'ACADEMIC', '#FF5733', 'MATH', false, false, 2),
('HEB101', 'עברית', 'Hébreu', 'LANGUAGE', '#3357FF', 'HEB', false, false, 2),
('FR101', 'צרפתית', 'Français', 'LANGUAGE', '#33FF57', 'FR', false, false, 2),
('ENG101', 'אנגלית', 'Anglais', 'LANGUAGE', '#FF33F5', 'ENG', false, false, 2),

-- Science Subjects
('SCI101', 'מדעים', 'Sciences', 'SCIENCE_LAB', '#FFD700', 'SCI', true, true, 2),
('PHYS101', 'פיזיקה', 'Physique', 'SCIENCE_LAB', '#8A2BE2', 'PHYS', true, true, 2),
('CHEM101', 'כימיה', 'Chimie', 'SCIENCE_LAB', '#00CED1', 'CHEM', true, true, 2),
('BIO101', 'ביולוגיה', 'Biologie', 'SCIENCE_LAB', '#32CD32', 'BIO', true, true, 2),

-- Social Studies and Humanities
('HIST101', 'היסטוריה', 'Histoire', 'ACADEMIC', '#CD853F', 'HIST', false, false, 2),
('GEO101', 'גיאוגרפיה', 'Géographie', 'ACADEMIC', '#40E0D0', 'GEO', false, false, 2),
('LIT101', 'ספרות', 'Littérature', 'LANGUAGE', '#DDA0DD', 'LIT', false, false, 2),

-- Arts and Special Subjects
('ART101', 'אמנות', 'Arts Plastiques', 'ART', '#FF6347', 'ART', false, true, 2),
('MUS101', 'מוזיקה', 'Musique', 'MUSIC', '#FFB6C1', 'MUS', false, true, 2),
('PE101', 'חינוך גופני', 'Éducation Physique', 'SPORTS', '#98FB98', 'PE', false, true, 2),

-- Religion and Ethics
('REL101', 'יהדות', 'Judaïsme', 'RELIGION', '#F0E68C', 'REL', false, false, 2),
('ETH101', 'אתיקה', 'Éthique', 'RELIGION', '#D2B48C', 'ETH', false, false, 1),

-- Technical Subjects
('COMP101', 'מחשבים', 'Informatique', 'TECHNICAL', '#4169E1', 'COMP', false, true, 2),
('TECH101', 'טכנולוגיה', 'Technologie', 'TECHNICAL', '#FF4500', 'TECH', false, true, 2);

-- =============================================================================
-- TEACHERS
-- =============================================================================

INSERT INTO teachers (code, first_name, last_name, email, phone, max_hours_per_week, max_hours_per_day, primary_language, can_teach_in_french, can_teach_in_hebrew) VALUES
-- Mathematics Teachers
('T001', 'שרה', 'כהן', 'sarah.cohen@school.edu', '050-1234567', 30, 8, 'he', false, true),
('T002', 'דוד', 'לוי', 'david.levy@school.edu', '050-2345678', 25, 7, 'he', false, true),
('T003', 'Marie', 'Dubois', 'marie.dubois@school.edu', '050-3456789', 28, 8, 'fr', true, true),

-- Language Teachers
('T004', 'רחל', 'אברהם', 'rachel.abraham@school.edu', '050-4567890', 32, 8, 'he', false, true),
('T005', 'יוסף', 'דוד', 'yosef.david@school.edu', '050-5678901', 30, 8, 'he', false, true),
('T006', 'Sophie', 'Martin', 'sophie.martin@school.edu', '050-6789012', 30, 8, 'fr', true, true),
('T007', 'Jean', 'Bernard', 'jean.bernard@school.edu', '050-7890123', 28, 7, 'fr', true, true),

-- Science Teachers
('T008', 'מרים', 'גולדברג', 'miriam.goldberg@school.edu', '050-8901234', 30, 8, 'he', false, true),
('T009', 'אברהם', 'רוזן', 'abraham.rosen@school.edu', '050-9012345', 25, 7, 'he', false, true),
('T010', 'Pierre', 'Laurent', 'pierre.laurent@school.edu', '050-0123456', 30, 8, 'fr', true, true),

-- Arts and Special Subjects
('T011', 'תמר', 'שמואל', 'tamar.samuel@school.edu', '050-1122334', 25, 6, 'he', false, true),
('T012', 'משה', 'גרין', 'moshe.green@school.edu', '050-2233445', 20, 6, 'he', false, true),
('T013', 'Isabelle', 'Moreau', 'isabelle.moreau@school.edu', '050-3344556', 25, 6, 'fr', true, true),

-- PE and Technical
('T014', 'עמית', 'בן-דוד', 'amit.bendavid@school.edu', '050-4455667', 30, 8, 'he', false, true),
('T015', 'רונית', 'כץ', 'ronit.katz@school.edu', '050-5566778', 25, 7, 'he', false, true);

-- =============================================================================
-- TEACHER-SUBJECT ASSIGNMENTS
-- =============================================================================

INSERT INTO teacher_subjects (teacher_id, subject_id, proficiency_level) VALUES
-- Mathematics Teachers
(1, 1, 10), -- Sarah Cohen - Math
(2, 1, 9),  -- David Levy - Math
(3, 1, 8),  -- Marie Dubois - Math

-- Language Teachers - Hebrew
(4, 2, 10), -- Rachel Abraham - Hebrew
(5, 2, 9),  -- Yosef David - Hebrew
(4, 11, 8), -- Rachel Abraham - Literature

-- Language Teachers - French
(6, 3, 10), -- Sophie Martin - French
(7, 3, 9),  -- Jean Bernard - French
(6, 11, 8), -- Sophie Martin - Literature

-- Language Teachers - English
(4, 4, 7),  -- Rachel Abraham - English
(6, 4, 9),  -- Sophie Martin - English
(7, 4, 8),  -- Jean Bernard - English

-- Science Teachers
(8, 5, 10), -- Miriam Goldberg - Science
(8, 6, 9),  -- Miriam Goldberg - Physics
(9, 7, 10), -- Abraham Rosen - Chemistry
(9, 8, 8),  -- Abraham Rosen - Biology
(10, 5, 9), -- Pierre Laurent - Science
(10, 6, 10), -- Pierre Laurent - Physics

-- Social Studies
(4, 9, 7),  -- Rachel Abraham - History
(5, 9, 8),  -- Yosef David - History
(6, 10, 8), -- Sophie Martin - Geography
(7, 10, 7), -- Jean Bernard - Geography

-- Arts and Special Subjects
(11, 12, 10), -- Tamar Samuel - Art
(12, 13, 10), -- Moshe Green - Music
(13, 13, 9),  -- Isabelle Moreau - Music
(13, 12, 7),  -- Isabelle Moreau - Art

-- PE and Technical
(14, 14, 10), -- Amit Ben-David - PE
(15, 14, 8),  -- Ronit Katz - PE
(15, 16, 9),  -- Ronit Katz - Computer
(9, 17, 7),   -- Abraham Rosen - Technology

-- Religion
(5, 15, 9),   -- Yosef David - Religion
(4, 16, 6);   -- Rachel Abraham - Ethics

-- =============================================================================
-- ROOMS
-- =============================================================================

INSERT INTO rooms (code, name_he, name_fr, room_type, capacity, floor_number, building, has_projector, has_computer, has_lab_equipment, is_accessible) VALUES
-- Regular Classrooms
('A101', 'כיתה א-1', 'Classe A-1', 'CLASSROOM', 30, 1, 'Building A', true, false, false, true),
('A102', 'כיתה א-2', 'Classe A-2', 'CLASSROOM', 32, 1, 'Building A', true, false, false, true),
('A103', 'כיתה א-3', 'Classe A-3', 'CLASSROOM', 28, 1, 'Building A', true, false, false, true),
('A201', 'כיתה א-4', 'Classe A-4', 'CLASSROOM', 30, 2, 'Building A', true, false, false, true),
('A202', 'כיתה א-5', 'Classe A-5', 'CLASSROOM', 30, 2, 'Building A', true, false, false, true),
('A203', 'כיתה א-6', 'Classe A-6', 'CLASSROOM', 30, 2, 'Building A', true, false, false, true),

-- Science Labs
('B101', 'מעבדת פיזיקה', 'Laboratoire de Physique', 'LAB', 24, 1, 'Building B', true, true, true, true),
('B102', 'מעבדת כימיה', 'Laboratoire de Chimie', 'LAB', 24, 1, 'Building B', true, true, true, true),
('B103', 'מעבדת ביולוגיה', 'Laboratoire de Biologie', 'LAB', 24, 1, 'Building B', true, true, true, true),
('B201', 'מעבדת מדעים כללית', 'Laboratoire Sciences Générales', 'LAB', 28, 2, 'Building B', true, true, true, true),

-- Special Rooms
('C101', 'חדר מחשבים', 'Salle Informatique', 'COMPUTER_ROOM', 25, 1, 'Building C', true, true, false, true),
('C102', 'אולם התעמלות', 'Gymnase', 'GYM', 60, 1, 'Building C', false, false, false, true),
('C201', 'חדר אמנות', 'Salle d\'Arts', 'ART_ROOM', 20, 2, 'Building C', false, false, false, true),
('C202', 'חדר מוזיקה', 'Salle de Musique', 'MUSIC_ROOM', 25, 2, 'Building C', true, true, false, true),

-- Library and Auditorium
('D101', 'ספרייה', 'Bibliothèque', 'LIBRARY', 40, 1, 'Building D', false, true, false, true),
('D201', 'אודיטוריום', 'Auditorium', 'AUDITORIUM', 120, 2, 'Building D', true, true, false, true);

-- =============================================================================
-- CLASS GROUPS
-- =============================================================================

INSERT INTO class_groups (code, name_he, name_fr, grade, class_type, student_count, max_capacity, primary_language, academic_year) VALUES
-- Elementary Classes
('CP-A', 'כיתה א', 'CP-A', 'CP', 25, 30, 'he', '2024-2025'),
('CP-B', 'כיתה א-ב', 'CP-B', 'CP', 24, 30, 'fr', '2024-2025'),
('CE1-A', 'כיתה ב', 'CE1-A', 'CE1', 26, 30, 'he', '2024-2025'),
('CE1-B', 'כיתה ב-ב', 'CE1-B', 'CE1', 25, 30, 'fr', '2024-2025'),
('CE2-A', 'כיתה ג', 'CE2-A', 'CE2', 27, 30, 'he', '2024-2025'),
('CE2-B', 'כיתה ג-ב', 'CE2-B', 'CE2', 26, 30, 'fr', '2024-2025'),

-- Middle School
('6A', 'כיתה ו', 'Sixième A', 'SIXIEME', 28, 32, 'he', '2024-2025'),
('6B', 'כיתה ו-ב', 'Sixième B', 'SIXIEME', 27, 32, 'fr', '2024-2025'),
('5A', 'כיתה ז', 'Cinquième A', 'CINQUIEME', 29, 32, 'he', '2024-2025'),
('5B', 'כיתה ז-ב', 'Cinquième B', 'CINQUIEME', 28, 32, 'fr', '2024-2025'),

-- High School
('3A', 'כיתה ט', 'Troisième A', 'TROISIEME', 26, 30, 'he', '2024-2025'),
('3B', 'כיתה ט-ב', 'Troisième B', 'TROISIEME', 25, 30, 'fr', '2024-2025'),
('2A', 'כיתה י', 'Seconde A', 'SECONDE', 24, 28, 'he', '2024-2025'),
('1A', 'כיתה יא', 'Première A', 'PREMIERE', 22, 26, 'he', '2024-2025'),
('TA', 'כיתה יב', 'Terminale A', 'TERMINALE', 20, 24, 'he', '2024-2025');

-- =============================================================================
-- CLASS SUBJECT REQUIREMENTS
-- =============================================================================

INSERT INTO class_subject_requirements (class_group_id, subject_id, hours_per_week, requires_double_period, max_consecutive_hours) VALUES
-- CP-A (Hebrew Primary)
(1, 1, 6, false, 2), -- Math
(1, 2, 8, false, 2), -- Hebrew
(1, 3, 4, false, 2), -- French
(1, 4, 3, false, 1), -- English
(1, 5, 3, false, 1), -- Science
(1, 14, 2, false, 1), -- PE
(1, 15, 2, false, 1), -- Religion

-- CP-B (French Primary)  
(2, 1, 6, false, 2), -- Math
(2, 2, 4, false, 2), -- Hebrew
(2, 3, 8, false, 2), -- French
(2, 4, 3, false, 1), -- English
(2, 5, 3, false, 1), -- Science
(2, 14, 2, false, 1), -- PE
(2, 15, 2, false, 1), -- Religion

-- 6A (Middle School Hebrew)
(7, 1, 5, false, 2), -- Math
(7, 2, 6, false, 2), -- Hebrew
(7, 3, 4, false, 2), -- French
(7, 4, 4, false, 2), -- English
(7, 5, 4, true, 2),  -- Science
(7, 9, 3, false, 2), -- History
(7, 10, 2, false, 1), -- Geography
(7, 14, 3, false, 1), -- PE
(7, 15, 2, false, 1), -- Religion

-- 3A (High School Hebrew)
(11, 1, 6, false, 2), -- Math
(11, 2, 5, false, 2), -- Hebrew
(11, 3, 4, false, 2), -- French
(11, 4, 4, false, 2), -- English
(11, 6, 3, true, 2),  -- Physics
(11, 7, 3, true, 2),  -- Chemistry
(11, 8, 3, true, 2),  -- Biology
(11, 9, 3, false, 2), -- History
(11, 10, 2, false, 1), -- Geography
(11, 14, 2, false, 1), -- PE
(11, 15, 1, false, 1); -- Religion

-- =============================================================================
-- TEACHER AVAILABILITY (Sample for a few teachers)
-- =============================================================================

INSERT INTO teacher_availability (teacher_id, day_of_week, start_time, end_time, is_available) VALUES
-- Sarah Cohen (T001) - Full availability except Friday afternoon
(1, 'SUNDAY', '08:00', '16:00', true),
(1, 'MONDAY', '08:00', '16:00', true),
(1, 'TUESDAY', '08:00', '16:00', true),
(1, 'WEDNESDAY', '08:00', '16:00', true),
(1, 'THURSDAY', '08:00', '16:00', true),
(1, 'FRIDAY', '08:00', '13:00', true),

-- David Levy (T002) - Not available Tuesday mornings
(2, 'SUNDAY', '08:00', '16:00', true),
(2, 'MONDAY', '08:00', '16:00', true),
(2, 'TUESDAY', '10:00', '16:00', true),
(2, 'WEDNESDAY', '08:00', '16:00', true),
(2, 'THURSDAY', '08:00', '16:00', true),
(2, 'FRIDAY', '08:00', '13:00', true),

-- Marie Dubois (T003) - Limited Friday availability
(3, 'SUNDAY', '08:00', '16:00', true),
(3, 'MONDAY', '08:00', '16:00', true),
(3, 'TUESDAY', '08:00', '16:00', true),
(3, 'WEDNESDAY', '08:00', '16:00', true),
(3, 'THURSDAY', '08:00', '16:00', true),
(3, 'FRIDAY', '08:00', '12:00', true);

-- =============================================================================
-- SAMPLE SCHEDULE
-- =============================================================================

INSERT INTO schedules (name, academic_year, semester, is_active, is_published, generated_by) VALUES
('מערכת שעות סמסטר א 2024-2025', '2024-2025', 1, true, false, 1);

-- =============================================================================
-- SAMPLE CONSTRAINTS
-- =============================================================================

INSERT INTO constraints (name, constraint_type, target_type, target_id, constraint_data, priority, is_active, created_by) VALUES
-- Teacher constraints
('Sarah Cohen - No teaching after 3 PM', 'TEACHER_AVAILABILITY', 'teacher', 1, '{"max_end_time": "15:00", "days": ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY"]}', 8, true, 1),
('Math classes should be in morning', 'SUBJECT_REQUIREMENT', 'subject', 1, '{"preferred_periods": [1, 2, 3, 4], "avoid_periods": [7, 8, 9, 10]}', 6, true, 1),
('Science labs need double periods', 'SUBJECT_REQUIREMENT', 'subject', 5, '{"requires_consecutive": true, "min_duration": 90}', 9, true, 1);

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

-- Update the setup user to indicate completion
UPDATE users SET full_name = 'Database Setup Complete', updated_at = CURRENT_TIMESTAMP WHERE username = 'setup';

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'School Timetable Generator database has been successfully initialized!';
    RAISE NOTICE 'Default admin credentials:';
    RAISE NOTICE '  Username: admin';
    RAISE NOTICE '  Password: admin123';
    RAISE NOTICE '  Email: admin@school.edu';
    RAISE NOTICE '';
    RAISE NOTICE 'Test data includes:';
    RAISE NOTICE '  - 15 teachers with various subjects';
    RAISE NOTICE '  - 17 subjects across all categories';
    RAISE NOTICE '  - 16 rooms including labs and special rooms';
    RAISE NOTICE '  - 15 class groups from CP to Terminale';
    RAISE NOTICE '  - Sample subject requirements and teacher availability';
    RAISE NOTICE '';
    RAISE NOTICE 'You can now start the application and begin scheduling!';
END
$$; 