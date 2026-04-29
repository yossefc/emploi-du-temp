"""
Endpoints for importing data from various sources.
Enhanced with comprehensive ETL system.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from io import BytesIO
import logging
import tempfile
import os

from app.db.base import get_db
from app.etl.shahaf_import import ShahafImporter
from app.etl.exceptions import ETLError, ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

# Legacy functions for backward compatibility
def parse_disponibilites(disponibilites_str: str) -> List[str]:
    """Parse disponibilités string into list"""
    if pd.isna(disponibilites_str) or not disponibilites_str:
        return []
    return [d.strip() for d in disponibilites_str.split(';')]

def parse_contraintes(contraintes_str: str) -> List[str]:
    """Parse contraintes string into list"""
    if pd.isna(contraintes_str) or not contraintes_str:
        return []
    return [c.strip() for c in contraintes_str.split(';')]

def validate_row(row: pd.Series, row_index: int) -> List[str]:
    """Validate a single row and return list of errors"""
    errors = []
    
    # Required fields validation
    prenom = row.get('prenom')
    if prenom is None or pd.isna(prenom) or not str(prenom).strip():
        errors.append(f"Ligne {row_index + 2}: Prénom requis")
    
    nom = row.get('nom')
    if nom is None or pd.isna(nom) or not str(nom).strip():
        errors.append(f"Ligne {row_index + 2}: Nom requis")
    
    classe = row.get('classe')
    if classe is None or pd.isna(classe) or not str(classe).strip():
        errors.append(f"Ligne {row_index + 2}: Classe requise")
    
    matiere = row.get('matiere')
    if matiere is None or pd.isna(matiere) or not str(matiere).strip():
        errors.append(f"Ligne {row_index + 2}: Matière requise")
    
    # Type classe validation
    type_classe = row.get('type_classe')
    if type_classe is not None and not pd.isna(type_classe) and type_classe not in ['classe', 'promotion']:
        errors.append(f"Ligne {row_index + 2}: type_classe doit être 'classe' ou 'promotion'")
    
    # Heures validation
    try:
        heures_val = row.get('heures_par_semaine', 0)
        if heures_val is not None and not pd.isna(heures_val):
            heures = int(float(heures_val))  # Convert to float first, then int
            if heures <= 0:
                errors.append(f"Ligne {row_index + 2}: heures_par_semaine doit être un entier positif")
        else:
            errors.append(f"Ligne {row_index + 2}: heures_par_semaine requis")
    except (ValueError, TypeError):
        errors.append(f"Ligne {row_index + 2}: heures_par_semaine doit être un nombre entier")
    
    return errors

def create_teacher_json(row: pd.Series) -> Dict[str, Any]:
    """Convert a row to teacher JSON format"""
    sous_matiere = row.get('sous_matiere', '')
    sous_matiere_value = "" if sous_matiere is None or pd.isna(sous_matiere) else str(sous_matiere).strip()
    
    heures_val = row.get('heures_par_semaine', 0)
    heures_value = 0 if heures_val is None or pd.isna(heures_val) else int(float(heures_val))
    
    return {
        "prenom": str(row['prenom']).strip(),
        "name": str(row['nom']).strip(),
        "classes": [{
            "promotion": str(row['classe']).strip(),
            "type": str(row.get('type_classe', 'classe')).strip()
        }],
        "matiere": str(row['matiere']).strip(),
        "sous_matiere": sous_matiere_value,
        "heures_par_semaine": heures_value,
        "disponibilites": parse_disponibilites(str(row.get('disponibilites', ''))),
        "contraintes_speciales": parse_contraintes(str(row.get('contraintes_speciales', '')))
    }

def generate_sql_insert(teacher_data: Dict[str, Any], teacher_id: int, classe_id: int) -> Dict[str, Any]:
    """Build a parameterized representation of the inserts for preview purposes.

    Returns a list of {sql, params} dicts using bound parameters — never use
    string concatenation here, the result is sometimes echoed back to clients
    and was previously vulnerable to SQL injection.
    """
    statements: List[Dict[str, Any]] = []

    statements.append({
        "sql": "INSERT INTO enseignants (prenom, nom) VALUES (:prenom, :nom)",
        "params": {"prenom": teacher_data['prenom'], "nom": teacher_data['nom']},
    })

    for classe in teacher_data['classes']:
        statements.append({
            "sql": "INSERT INTO classes (promotion, type) VALUES (:promotion, :type)",
            "params": {"promotion": classe['promotion'], "type": classe['type']},
        })

    statements.append({
        "sql": (
            "INSERT INTO cours (enseignant_id, classe_id, matiere, sous_matiere, heures_par_semaine) "
            "VALUES (:teacher_id, :classe_id, :matiere, :sous_matiere, :heures)"
        ),
        "params": {
            "teacher_id": teacher_id,
            "classe_id": classe_id,
            "matiere": teacher_data['matiere'],
            "sous_matiere": teacher_data['sous_matiere'],
            "heures": teacher_data['heures_par_semaine'],
        },
    })

    for dispo in teacher_data['disponibilites']:
        statements.append({
            "sql": "INSERT INTO disponibilites (enseignant_id, creneau) VALUES (:teacher_id, :creneau)",
            "params": {"teacher_id": teacher_id, "creneau": dispo},
        })

    for contrainte in teacher_data['contraintes_speciales']:
        statements.append({
            "sql": "INSERT INTO contraintes (enseignant_id, contrainte) VALUES (:teacher_id, :contrainte)",
            "params": {"teacher_id": teacher_id, "contrainte": contrainte},
        })

    return {"statements": statements}

# New ETL-based endpoints

@router.post("/import-complete-shahaf")
async def import_complete_shahaf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import complet depuis un fichier JSON d'export Shahaf.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier requis")
    
    if not file.filename.lower().endswith('.json'):
        raise HTTPException(status_code=400, detail="Format de fichier JSON requis")
    
    try:
        # Sauvegarder le fichier temporairement
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_file.write(content.decode('utf-8'))
            tmp_file_path = tmp_file.name
        
        try:
            # Utiliser le ShahafImporter
            importer = ShahafImporter(db)
            result = importer.import_from_json(tmp_file_path)
            
            return JSONResponse({
                "status": "success" if result["total_errors"] == 0 else "partial_success",
                "summary": result,
                "message": f"Import terminé avec {result['total_errors']} erreurs"
            })
            
        finally:
            # Nettoyer le fichier temporaire
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Erreur lors de l'import Shahaf: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@router.post("/import-subjects")
async def import_subjects(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import des matières depuis un fichier CSV/Excel.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier requis")
    
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ['xlsx', 'xls', 'csv']:
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv")
    
    try:
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            importer = ShahafImporter(db)
            result = importer.import_from_csv(tmp_file_path, 'subjects')
            
            return JSONResponse({
                "status": "success" if result["total_errors"] == 0 else "partial_success",
                "summary": result,
                "message": f"Import des matières terminé avec {result['total_errors']} erreurs"
            })
            
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Erreur lors de l'import des matières: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@router.post("/import-classes")
async def import_classes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import des classes depuis un fichier CSV/Excel.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier requis")
    
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ['xlsx', 'xls', 'csv']:
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv")
    
    try:
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            importer = ShahafImporter(db)
            result = importer.import_from_csv(tmp_file_path, 'classes')
            
            return JSONResponse({
                "status": "success" if result["total_errors"] == 0 else "partial_success",
                "summary": result,
                "message": f"Import des classes terminé avec {result['total_errors']} erreurs"
            })
            
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Erreur lors de l'import des classes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@router.post("/import-rooms")
async def import_rooms(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import des salles depuis un fichier CSV/Excel.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier requis")
    
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ['xlsx', 'xls', 'csv']:
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv")
    
    try:
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            importer = ShahafImporter(db)
            result = importer.import_from_csv(tmp_file_path, 'rooms')
            
            return JSONResponse({
                "status": "success" if result["total_errors"] == 0 else "partial_success",
                "summary": result,
                "message": f"Import des salles terminé avec {result['total_errors']} erreurs"
            })
            
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Erreur lors de l'import des salles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@router.post("/import-enhanced-teachers")
async def import_enhanced_teachers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import amélioré des enseignants utilisant le système ETL.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier requis")
    
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ['xlsx', 'xls', 'csv']:
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv")
    
    try:
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            importer = ShahafImporter(db)
            result = importer.import_from_csv(tmp_file_path, 'teachers')
            
            return JSONResponse({
                "status": "success" if result["total_errors"] == 0 else "partial_success",
                "summary": result,
                "message": f"Import des enseignants terminé avec {result['total_errors']} erreurs"
            })
            
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Erreur lors de l'import des enseignants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@router.get("/import-status/{import_id}")
async def get_import_status(
    import_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère le statut d'un import en cours.
    """
    # Cette fonctionnalité peut être implémentée avec un système de cache
    # ou une base de données pour suivre les imports en cours
    return JSONResponse({
        "import_id": import_id,
        "status": "in_progress",
        "progress": 50,
        "message": "Import en cours..."
    })

@router.post("/validate-import-data")
async def validate_import_data(
    file: UploadFile = File(...),
    data_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Valide les données d'import sans les importer.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier requis")
    
    if data_type not in ['teachers', 'subjects', 'classes', 'rooms']:
        raise HTTPException(status_code=400, detail="Type de données non supporté")
    
    try:
        content = await file.read()
        
        # Validation selon le type de données
        if file.filename.lower().endswith('.json'):
            data = json.loads(content.decode('utf-8'))
            importer = ShahafImporter(db)
            is_valid = importer.validate_data(data)
            
            validation_result = {
                "is_valid": is_valid,
                "errors": [str(e) for e in importer.errors],
                "warnings": importer.warnings
            }
        else:
            # Pour les fichiers CSV/Excel, faire une validation basique
            file_extension = file.filename.lower().split('.')[-1]
            if file_extension == 'csv':
                df = pd.read_csv(BytesIO(content))
            else:
                df = pd.read_excel(BytesIO(content))
            
            validation_result = {
                "is_valid": True,
                "rows_count": len(df),
                "columns": list(df.columns),
                "errors": [],
                "warnings": []
            }
        
        return JSONResponse(validation_result)
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la validation: {str(e)}")

# Legacy endpoints for backward compatibility

@router.post("/import-teachers")
async def import_teachers_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import teachers data from Excel or CSV file (legacy version)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier requis")
    
    # Check file format
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ['xlsx', 'xls', 'csv']:
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv")
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse file based on format
        if file_extension == 'csv':
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))
        
        # Check required columns
        required_columns = ['prenom', 'nom', 'classe', 'matiere', 'heures_par_semaine']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Colonnes manquantes: {', '.join(missing_columns)}"
            )
        
        # Process data
        import_data = []
        errors = []
        
        for idx, (index, row) in enumerate(df.iterrows()):
            # Validate row
            row_errors = validate_row(row, idx)
            if row_errors:
                errors.extend(row_errors)
                continue
            
            try:
                # Create teacher JSON
                teacher_json = create_teacher_json(row)
                
                # Generate SQL (mock IDs for example)
                teacher_id = idx + 1
                classe_id = idx + 1
                sql_insert = generate_sql_insert(teacher_json, teacher_id, classe_id)
                
                import_data.append({
                    "json": teacher_json,
                    "sql_insert": sql_insert
                })
                
            except Exception as e:
                errors.append(f"Ligne {idx + 2}: Erreur de traitement - {str(e)}")
        
        return JSONResponse({
            "import": import_data,
            "errors": errors,
            "summary": {
                "total_rows": len(df),
                "successful_imports": len(import_data),
                "errors_count": len(errors)
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'importation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du fichier: {str(e)}")

@router.post("/import-teachers/execute")
async def execute_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import and save teachers data to database (legacy version)
    """
    # This would contain the actual database insertion logic
    # For now, returning the import preview
    return await import_teachers_file(file, db) 