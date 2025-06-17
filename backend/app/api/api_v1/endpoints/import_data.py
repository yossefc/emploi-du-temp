from typing import List, Dict, Any, Optional
import pandas as pd
import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from io import BytesIO
import logging

from app.db.base import get_db
from app.models.teacher import Teacher
from app.models.class_group import ClassGroup
from app.models.subject import Subject
from app.schemas.teacher import TeacherCreate
from app.schemas.class_group import ClassGroupCreate
from app.schemas.subject import SubjectCreate

router = APIRouter()
logger = logging.getLogger(__name__)

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
    if pd.isna(row.get('prenom')) or not str(row.get('prenom')).strip():
        errors.append(f"Ligne {row_index + 2}: Prénom requis")
    
    if pd.isna(row.get('nom')) or not str(row.get('nom')).strip():
        errors.append(f"Ligne {row_index + 2}: Nom requis")
    
    if pd.isna(row.get('classe')) or not str(row.get('classe')).strip():
        errors.append(f"Ligne {row_index + 2}: Classe requise")
    
    if pd.isna(row.get('matiere')) or not str(row.get('matiere')).strip():
        errors.append(f"Ligne {row_index + 2}: Matière requise")
    
    # Type classe validation
    type_classe = row.get('type_classe')
    if pd.notna(type_classe) and type_classe not in ['classe', 'promotion']:
        errors.append(f"Ligne {row_index + 2}: type_classe doit être 'classe' ou 'promotion'")
    
    # Heures validation
    try:
        heures = int(row.get('heures_par_semaine', 0))
        if heures <= 0:
            errors.append(f"Ligne {row_index + 2}: heures_par_semaine doit être un entier positif")
    except (ValueError, TypeError):
        errors.append(f"Ligne {row_index + 2}: heures_par_semaine doit être un nombre entier")
    
    return errors

def create_teacher_json(row: pd.Series) -> Dict[str, Any]:
    """Convert a row to teacher JSON format"""
    return {
        "prenom": str(row['prenom']).strip(),
        "nom": str(row['nom']).strip(),
        "classes": [{
            "promotion": str(row['classe']).strip(),
            "type": str(row.get('type_classe', 'classe')).strip()
        }],
        "matiere": str(row['matiere']).strip(),
        "sous_matiere": str(row.get('sous_matiere', '')).strip() if pd.notna(row.get('sous_matiere')) else "",
        "heures_par_semaine": int(row.get('heures_par_semaine', 0)),
        "disponibilites": parse_disponibilites(str(row.get('disponibilites', ''))),
        "contraintes_speciales": parse_contraintes(str(row.get('contraintes_speciales', '')))
    }

def generate_sql_insert(teacher_data: Dict[str, Any], teacher_id: int, classe_id: int) -> str:
    """Generate SQL INSERT statements for teacher data"""
    sql_statements = []
    
    # Insert teacher
    sql_statements.append(
        f"INSERT INTO enseignants (prenom, nom) VALUES ('{teacher_data['prenom']}', '{teacher_data['nom']}');"
    )
    
    # Insert class if needed
    for classe in teacher_data['classes']:
        sql_statements.append(
            f"INSERT INTO classes (promotion, type) VALUES ('{classe['promotion']}', '{classe['type']}');"
        )
    
    # Insert cours
    sql_statements.append(
        f"INSERT INTO cours (enseignant_id, classe_id, matiere, sous_matiere, heures_par_semaine) "
        f"VALUES ({teacher_id}, {classe_id}, '{teacher_data['matiere']}', '{teacher_data['sous_matiere']}', {teacher_data['heures_par_semaine']});"
    )
    
    # Insert disponibilites
    for dispo in teacher_data['disponibilites']:
        sql_statements.append(
            f"INSERT INTO disponibilites (enseignant_id, creneau) VALUES ({teacher_id}, '{dispo}');"
        )
    
    # Insert contraintes
    for contrainte in teacher_data['contraintes_speciales']:
        sql_statements.append(
            f"INSERT INTO contraintes (enseignant_id, contrainte) VALUES ({teacher_id}, '{contrainte}');"
        )
    
    return " ".join(sql_statements)

@router.post("/import-teachers")
async def import_teachers_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import teachers data from Excel or CSV file
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
        
        for index, row in df.iterrows():
            # Validate row
            row_errors = validate_row(row, index)
            if row_errors:
                errors.extend(row_errors)
                continue
            
            try:
                # Create teacher JSON
                teacher_json = create_teacher_json(row)
                
                # Generate SQL (mock IDs for example)
                teacher_id = index + 1
                classe_id = index + 1
                sql_insert = generate_sql_insert(teacher_json, teacher_id, classe_id)
                
                import_data.append({
                    "json": teacher_json,
                    "sql_insert": sql_insert
                })
                
            except Exception as e:
                errors.append(f"Ligne {index + 2}: Erreur de traitement - {str(e)}")
        
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
    Import and save teachers data to database
    """
    # This would contain the actual database insertion logic
    # For now, returning the import preview
    return await import_teachers_file(file, db) 