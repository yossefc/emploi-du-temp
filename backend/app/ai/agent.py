"""
Agent IA pour l'assistance à la génération d'emplois du temps.
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import anthropic
import openai
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.models.schedule import Schedule, ScheduleEntry

logger = logging.getLogger(__name__)


class TimetableAIAgent:
    """Agent IA pour assister dans la création et l'optimisation d'emplois du temps."""
    
    def __init__(self, db: Session):
        self.db = db
        self.use_claude = settings.USE_CLAUDE
        
        if self.use_claude:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            openai.api_key = settings.OPENAI_API_KEY
    
    async def send_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Envoyer un message à l'agent IA et recevoir une réponse.
        """
        try:
            # Préparer le contexte
            system_prompt = self._prepare_system_prompt(context)
            
            if self.use_claude:
                response = await self._send_to_claude(message, system_prompt)
            else:
                response = await self._send_to_gpt(message, system_prompt)
            
            # Parser la réponse et extraire les actions
            parsed_response = self._parse_ai_response(response)
            
            return {
                "message": parsed_response["message"],
                "suggestions": parsed_response.get("suggestions", []),
                "actions": parsed_response.get("actions", []),
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Error in AI agent: {str(e)}")
            return {
                "message": "Désolé, une erreur s'est produite. Pouvez-vous reformuler votre demande ?",
                "suggestions": [],
                "actions": [],
                "error": str(e)
            }
    
    def _prepare_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Préparer le prompt système avec le contexte."""
        base_prompt = """
Tu es un assistant IA spécialisé dans la création d'emplois du temps scolaires.
Tu aides les utilisateurs à :
1. Comprendre et résoudre les conflits d'emploi du temps
2. Ajouter des contraintes en langage naturel
3. Optimiser la répartition des cours
4. Expliquer les décisions du système d'optimisation

Spécificités du système éducatif israélien :
- La semaine va du dimanche au vendredi
- Le vendredi se termine à 13h (6 périodes max)
- Possibilité de séparer garçons/filles pour certains cours
- Support bilingue français/hébreu

Tu dois toujours répondre de manière claire et concise, en proposant des actions concrètes.
Si tu identifies des contraintes dans le message, formate-les en JSON.
"""
        
        if context:
            if context.get("schedule_id"):
                schedule = self.db.query(Schedule).filter(Schedule.id == context["schedule_id"]).first()
                if schedule:
                    base_prompt += f"\n\nContexte actuel : Emploi du temps '{schedule.name}'"
                    if schedule.conflicts:
                        base_prompt += f"\nConflits détectés : {len(schedule.conflicts)}"
        
        return base_prompt
    
    async def _send_to_claude(self, message: str, system_prompt: str) -> str:
        """Envoyer le message à Claude."""
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": message}
            ]
        )
        return response.content[0].text
    
    async def _send_to_gpt(self, message: str, system_prompt: str) -> str:
        """Envoyer le message à GPT."""
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parser la réponse de l'IA pour extraire les actions structurées."""
        result = {
            "message": response,
            "suggestions": [],
            "actions": []
        }
        
        # Essayer d'extraire du JSON de la réponse
        try:
            # Chercher des blocs JSON dans la réponse
            import re
            json_pattern = r'\{[^{}]*\}'
            json_matches = re.findall(json_pattern, response)
            
            for match in json_matches:
                try:
                    data = json.loads(match)
                    if "action" in data:
                        result["actions"].append(data)
                    elif "suggestion" in data:
                        result["suggestions"].append(data["suggestion"])
                except:
                    pass
        except:
            pass
        
        # Si pas de suggestions trouvées, en générer quelques-unes par défaut
        if not result["suggestions"] and "conflit" in response.lower():
            result["suggestions"] = [
                "Voir les détails du conflit",
                "Proposer une alternative",
                "Ignorer ce conflit"
            ]
        
        return result
    
    async def parse_constraints(self, text: str) -> Dict[str, Any]:
        """
        Parser du texte en langage naturel pour extraire des contraintes.
        """
        system_prompt = """
Tu es un expert en parsing de contraintes d'emploi du temps.
Extrais toutes les contraintes mentionnées dans le texte et formate-les en JSON.

Format de sortie attendu :
{
    "constraints": [
        {
            "type": "teacher_availability" | "room_unavailability" | "consecutive_hours" | "max_hours_per_day" | "other",
            "entity": "nom de l'entité concernée",
            "description": "description en français",
            "parameters": {
                // paramètres spécifiques selon le type
            }
        }
    ]
}

Exemples :
- "Le professeur Dupont ne peut pas enseigner le lundi matin" -> teacher_availability
- "La salle 101 est réservée tous les mercredis" -> room_unavailability
- "Les cours de math doivent être consécutifs" -> consecutive_hours
"""
        
        try:
            if self.use_claude:
                response = await self._send_to_claude(text, system_prompt)
            else:
                response = await self._send_to_gpt(text, system_prompt)
            
            # Extraire le JSON de la réponse
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                constraints_data = json.loads(json_match.group())
                return constraints_data
            else:
                return {"constraints": [], "error": "Impossible d'extraire les contraintes"}
                
        except Exception as e:
            logger.error(f"Error parsing constraints: {str(e)}")
            return {"constraints": [], "error": str(e)}
    
    async def explain_conflict(self, conflict_id: int) -> Dict[str, Any]:
        """
        Expliquer un conflit de manière compréhensible.
        """
        # Récupérer le conflit depuis la DB
        # Pour l'instant, on simule
        conflict_description = f"Conflit #{conflict_id}: L'enseignant est assigné à deux classes en même temps"
        
        explanation = f"""
Je vais vous expliquer ce conflit de manière simple :

{conflict_description}

**Pourquoi est-ce un problème ?**
Un enseignant ne peut pas être dans deux endroits différents au même moment.

**Solutions possibles :**
1. Déplacer l'un des cours à un autre créneau horaire
2. Assigner un autre enseignant à l'un des cours
3. Fusionner les deux classes si c'est la même matière

Voulez-vous que je propose une modification spécifique ?
"""
        
        return {
            "explanation": explanation,
            "suggestions": [
                "Déplacer le premier cours",
                "Déplacer le second cours",
                "Changer d'enseignant",
                "Voir les créneaux disponibles"
            ]
        }
    
    async def get_suggestions(self, schedule_id: int) -> List[Dict[str, Any]]:
        """
        Obtenir des suggestions d'amélioration pour un emploi du temps.
        """
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            return []
        
        suggestions = []
        
        # Analyser l'emploi du temps et générer des suggestions
        entries = self.db.query(ScheduleEntry).filter(
            ScheduleEntry.schedule_id == schedule_id
        ).all()
        
        # Suggestion 1: Équilibrer la charge
        teacher_load = {}
        for entry in entries:
            if entry.teacher_id not in teacher_load:
                teacher_load[entry.teacher_id] = 0
            teacher_load[entry.teacher_id] += 1
        
        max_load = max(teacher_load.values()) if teacher_load else 0
        min_load = min(teacher_load.values()) if teacher_load else 0
        
        if max_load - min_load > 5:
            suggestions.append({
                "id": 1,
                "type": "optimization",
                "description": "Certains enseignants ont une charge significativement plus élevée que d'autres",
                "priority": "medium",
                "action": {
                    "type": "rebalance_load",
                    "parameters": {"threshold": 5}
                }
            })
        
        # Suggestion 2: Réduire les trous
        # (Analyse simplifiée - à améliorer)
        suggestions.append({
            "id": 2,
            "type": "optimization",
            "description": "Optimiser pour réduire les périodes libres entre les cours",
            "priority": "low",
            "action": {
                "type": "minimize_gaps",
                "parameters": {}
            }
        })
        
        return suggestions


# Alias pour compatibilité avec les imports existants
AIAgent = TimetableAIAgent 