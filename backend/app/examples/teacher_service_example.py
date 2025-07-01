"""
Example usage of the Teacher service layer with dependency injection.
"""

from sqlalchemy.orm import Session
from app.repositories.teacher_repository import TeacherRepository
from app.services.teacher_service import TeacherService
from app.core.exceptions import ValidationException, BusinessRuleException, NotFoundException, DuplicateException


def get_teacher_service(db: Session) -> TeacherService:
    """
    Factory function to create TeacherService with dependency injection.
    
    Args:
        db: Database session
        
    Returns:
        Configured TeacherService instance
    """
    teacher_repository = TeacherRepository(db)
    return TeacherService(teacher_repository)


def example_usage(db: Session):
    """Example of using the teacher service."""
    
    # Get service instance
    teacher_service = get_teacher_service(db)
    
    # 1. Create a new teacher
    teacher_data = {
        "code": "MATH001",
        "first_name": "Sarah",
        "last_name": "Cohen",
        "email": "sarah.cohen@school.edu",
        "phone": "+972-50-1234567",
        "max_hours_per_week": 25,
        "max_hours_per_day": 6,
        "contract_type": "full_time",
        "hire_date": "2024-09-01",
        "can_teach_in_hebrew": True,
        "can_teach_in_french": False,
        "primary_language": "he"
    }
    
    try:
        # Service handles validation, business rules, and persistence
        new_teacher = teacher_service.create(teacher_data)
        print(f"Created teacher: {new_teacher}")
        
    except ValidationException as e:
        print(f"Validation error: {e.message}")
        if e.validation_errors:
            for field, error in e.validation_errors.items():
                print(f"  {field}: {error}")
                
    except BusinessRuleException as e:
        print(f"Business rule violation: {e.message}")
        
    # 2. Search for teachers
    search_results = teacher_service.search_teachers("Cohen")
    print(f"Found {len(search_results)} teachers matching 'Cohen'")
    
    # 3. Get teachers by subject
    math_teachers = teacher_service.get_teachers_by_subject(subject_id=1)
    print(f"Math teachers: {[t.display_name for t in math_teachers]}")
    
    # 4. Get bilingual teachers
    bilingual_teachers = teacher_service.get_bilingual_teachers()
    print(f"Bilingual teachers: {[t.display_name for t in bilingual_teachers]}")
    
    # 5. Update teacher information
    if new_teacher:
        try:
            updated_teacher = teacher_service.update(new_teacher.id, {
                "max_hours_per_week": 30,
                "notes": "Experienced mathematics teacher"
            })
            print(f"Updated teacher: {updated_teacher}")
            
        except ValidationException as e:
            print(f"Update validation error: {e.message}")
    
    # 6. Assign subjects to teacher
    if new_teacher:
        try:
            teacher_with_subjects = teacher_service.assign_subjects(
                teacher_id=new_teacher.id,
                subject_ids=[1, 2, 3]  # Math, Algebra, Geometry
            )
            print(f"Assigned subjects to {teacher_with_subjects.display_name}")
            
        except BusinessRuleException as e:
            print(f"Cannot assign subjects: {e.message}")
    
    # 7. Get teacher workload
    if new_teacher:
        workload = teacher_service.get_teacher_workload(new_teacher.id)
        print(f"Teacher workload: {workload}")
    
    # 8. Get teachers summary
    summary = teacher_service.get_teachers_summary()
    print(f"Teachers summary: {summary}")
    
    # 9. Handle teacher deactivation
    if new_teacher:
        try:
            deactivated_teacher = teacher_service.deactivate_teacher(
                teacher_id=new_teacher.id,
                reason="End of contract"
            )
            print(f"Deactivated teacher: {deactivated_teacher.display_name}")
            
        except BusinessRuleException as e:
            print(f"Cannot deactivate: {e.message}")


def example_error_handling(db: Session):
    """Example of comprehensive error handling."""
    
    teacher_service = get_teacher_service(db)
    
    # Example 1: Validation errors
    try:
        teacher_service.create({
            "code": "",  # Invalid: empty code
            "first_name": "John",
            # Missing required fields
        })
    except ValidationException as e:
        print(f"Validation failed: {e.message}")
        print(f"Error code: {e.error_code}")
        print(f"Details: {e.details}")
    
    # Example 2: Duplicate teacher
    try:
        teacher_service.create({
            "code": "EXISTING_CODE",  # Assuming this exists
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@school.edu"
        })
    except DuplicateException as e:
        print(f"Duplicate resource: {e.message}")
        print(f"Resource type: {e.resource_type}")
        print(f"Field: {e.field}")
        print(f"Value: {e.value}")
    
    # Example 3: Not found
    try:
        teacher_service.get_by_id_or_raise(99999)  # Non-existent ID
    except NotFoundException as e:
        print(f"Resource not found: {e.message}")
        print(f"Resource type: {e.resource_type}")
        print(f"Identifier: {e.identifier}")
    
    # Example 4: Business rule violation
    try:
        # Try to assign subjects to inactive teacher
        teacher_service.assign_subjects(
            teacher_id=1,  # Assuming this is an inactive teacher
            subject_ids=[1, 2]
        )
    except BusinessRuleException as e:
        print(f"Business rule violation: {e.message}")
        print(f"Rule name: {e.rule_name}")


def example_pagination_and_filtering(db: Session):
    """Example of pagination and filtering."""
    
    teacher_service = get_teacher_service(db)
    
    # Get active teachers with pagination
    page_1 = teacher_service.get_all(
        skip=0,
        limit=10,
        order_by="last_name",
        desc_order=False,
        filters={"is_active": True}
    )
    
    page_2 = teacher_service.get_all(
        skip=10,
        limit=10,
        order_by="last_name",
        desc_order=False,
        filters={"is_active": True}
    )
    
    # Count total active teachers
    total_active = teacher_service.count({"is_active": True})
    
    print(f"Page 1: {len(page_1)} teachers")
    print(f"Page 2: {len(page_2)} teachers")
    print(f"Total active teachers: {total_active}")
    
    # Get teachers by contract type
    full_time_teachers = teacher_service.get_all(
        filters={"contract_type": "full_time", "is_active": True}
    )
    print(f"Full-time teachers: {len(full_time_teachers)}")


if __name__ == "__main__":
    # This would be called with a real database session
    # from app.core.database import get_db_session
    # 
    # with get_db_session() as db:
    #     example_usage(db)
    #     example_error_handling(db)
    #     example_pagination_and_filtering(db)
    
    print("Teacher service examples ready to run with database session") 