"""
Timetable solver module.

This module provides different timetable solvers:
- SimplifiedTimetableSolver: Robust, simplified solver with essential constraints
- TimetableSolver: Basic solver (minimal implementation)
- TimetableSolverComplete: Complex solver (has issues, deprecated)
"""

from .simplified_solver import SimplifiedTimetableSolver
from .timetable_solver import TimetableSolver

# Import for backwards compatibility (but has issues)
try:
    from .timetable_solver_complete import TimetableSolver as TimetableSolverComplete
except ImportError:
    TimetableSolverComplete = None

__all__ = [
    'SimplifiedTimetableSolver',
    'TimetableSolver', 
    'TimetableSolverComplete',
    'get_solver'
]


def get_solver(db_session, solver_type='simplified'):
    """
    Factory function to get the appropriate solver.
    
    Args:
        db_session: SQLAlchemy database session
        solver_type: Type of solver to use ('simplified', 'basic', 'complete')
    
    Returns:
        Solver instance
    
    Raises:
        ValueError: If solver_type is not recognized
    """
    if solver_type == 'simplified':
        return SimplifiedTimetableSolver(db_session)
    elif solver_type == 'basic':
        return TimetableSolver(db_session)
    elif solver_type == 'complete':
        if TimetableSolverComplete:
            return TimetableSolverComplete(db_session)
        else:
            raise ImportError("Complete solver not available")
    else:
        raise ValueError(f"Unknown solver type: {solver_type}. Use 'simplified', 'basic', or 'complete'") 