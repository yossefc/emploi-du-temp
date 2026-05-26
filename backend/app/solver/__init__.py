"""Moteur de génération d'emplois du temps — v2.

Architecture en deux couches :

1. **Constraints** (.constraints) — déclaration des règles métier.
   Chaque type de contrainte est une classe qui sait s'ajouter au modèle
   CP-SAT et s'expliquer en langage humain pour le dialogue conflit.

2. **Engine** (.engine) — orchestrateur :
   - Lit les Constraints de la DB
   - Construit le SolverContext (modèle CP-SAT + variables)
   - Applique toutes les Constraints
   - Lance le solve, extrait MUS si infeasible
   - Sauvegarde la solution
"""

from app.solver.context import SolverContext
from app.solver.engine import (
    ConflictItem,
    SolveConflict,
    SolveResult,
    SolveSuccess,
    SolveTimeout,
    TimetableEngine,
)

__all__ = [
    "SolverContext",
    "TimetableEngine",
    "SolveResult",
    "SolveSuccess",
    "SolveConflict",
    "SolveTimeout",
    "ConflictItem",
]
