"""
Test script for the SimplifiedTimetableSolver.

Run this script to test the solver functionality:
    python -m app.solver.test_solver
"""

import logging
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.solver.simplified_solver import SimplifiedTimetableSolver

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_simplified_solver():
    """Test the simplified timetable solver."""
    print("🚀 Testing SimplifiedTimetableSolver...")
    
    # Get database session (adjust based on your setup)
    db = next(get_db())
    
    try:
        # Initialize solver
        solver = SimplifiedTimetableSolver(db)
        
        # Run solver with 30 second time limit
        print("⏳ Starting solver (30s time limit)...")
        result = solver.solve(time_limit_seconds=30)
        
        # Display results
        print(f"\n📊 Solver Results:")
        print(f"Status: {result['status']}")
        print(f"Solution time: {result['solution_time']:.2f} seconds")
        print(f"Number of assignments: {len(result['assignments'])}")
        print(f"Number of conflicts: {len(result['conflicts'])}")
        
        # Show statistics
        if 'statistics' in result:
            stats = result['statistics']
            print(f"\n📈 Statistics:")
            print(f"Variables created: {stats['num_variables']}")
            print(f"Branches explored: {stats['num_branches']}")
            print(f"Conflicts: {stats['num_conflicts']}")
            print(f"Wall time: {stats['wall_time']:.2f}s")
        
        # Show sample assignments
        if result['assignments']:
            print(f"\n📋 First 5 assignments:")
            for i, assignment in enumerate(result['assignments'][:5]):
                print(f"  {i+1}. Class {assignment['class_id']} - "
                      f"{assignment['day']} P{assignment['period']} - "
                      f"Teacher {assignment['teacher_id']} - "
                      f"Subject {assignment['subject_id']} - "
                      f"Room {assignment['room_id']} - "
                      f"{assignment['start_time']}-{assignment['end_time']}")
        
        # Show conflicts
        if result['conflicts']:
            print(f"\n⚠️ Conflicts:")
            for i, conflict in enumerate(result['conflicts'][:3]):
                print(f"  {i+1}. {conflict['type']}: {conflict['description']}")
        
        # Show errors
        if 'errors' in result and result['errors']:
            print(f"\n❌ Errors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        return result
        
    finally:
        db.close()

if __name__ == "__main__":
    try:
        result = test_simplified_solver()
        
        if result['status'] in ['optimal', 'feasible']:
            print(f"\n✅ Success! Timetable generated.")
        elif result['status'] == 'infeasible':
            print(f"\n❌ No valid timetable possible with current constraints.")
        else:
            print(f"\n⚠️ Solver status: {result['status']}")
        
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc() 