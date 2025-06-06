"""
AI Agent for natural language processing and schedule optimization.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

import anthropic
import openai
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    Teacher, Subject, ClassGroup, Room,
    TeacherAvailability, GlobalConstraint,
    Schedule, ScheduleConflict
)

logger = logging.getLogger(__name__)


class ConversationRole(str, Enum):
    """Conversation roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Chat message structure."""
    role: ConversationRole
    content: str
    language: str = "he"  # Default Hebrew


@dataclass
class ConstraintParsed:
    """Parsed constraint from natural language."""
    entity_type: str  # teacher, class, room, global
    entity_id: Optional[int]
    constraint_type: str  # availability, preference, requirement
    parameters: Dict[str, Any]
    confidence: float  # 0-1 confidence score


class AIAgent:
    """Main AI agent for schedule management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.conversation_history: List[Message] = []
        
        # Initialize AI client based on settings
        if settings.USE_CLAUDE:
            self.client = anthropic.Client(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.AI_MODEL
        else:
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai
            self.model = settings.AI_MODEL
    
    async def process_message(
        self, 
        user_message: str, 
        language: str = "he",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return AI response with actions.
        """
        # Add user message to history
        self.conversation_history.append(
            Message(role=ConversationRole.USER, content=user_message, language=language)
        )
        
        # Determine intent
        intent = await self._determine_intent(user_message, language)
        
        # Process based on intent
        response = None
        actions = []
        
        if intent == "add_constraint":
            constraint = await self._parse_constraint(user_message, language)
            if constraint:
                actions.append({
                    "type": "add_constraint",
                    "data": constraint
                })
                response = self._generate_constraint_confirmation(constraint, language)
        
        elif intent == "explain_conflict":
            conflicts = context.get("conflicts", []) if context else []
            response = await self._explain_conflicts(conflicts, language)
        
        elif intent == "suggest_modification":
            schedule_data = context.get("schedule", {}) if context else {}
            suggestions = await self._generate_suggestions(schedule_data, language)
            actions.append({
                "type": "suggestions",
                "data": suggestions
            })
            response = self._format_suggestions(suggestions, language)
        
        elif intent == "query_schedule":
            query_result = await self._query_schedule(user_message, context, language)
            response = query_result["response"]
            if "visualization" in query_result:
                actions.append({
                    "type": "visualize",
                    "data": query_result["visualization"]
                })
        
        else:
            # General conversation
            response = await self._generate_response(user_message, language)
        
        # Add assistant response to history
        self.conversation_history.append(
            Message(role=ConversationRole.ASSISTANT, content=response, language=language)
        )
        
        return {
            "response": response,
            "actions": actions,
            "intent": intent
        }
    
    async def _determine_intent(self, message: str, language: str) -> str:
        """Determine the intent of the user message."""
        system_prompt = self._get_intent_system_prompt(language)
        
        if settings.USE_CLAUDE:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0.1,
                system=system_prompt,
                messages=[{"role": "user", "content": message}]
            )
            intent = response.content[0].text.strip().lower()
        else:
            response = self.client.ChatCompletion.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            intent = response.choices[0].message.content.strip().lower()
        
        # Map to known intents
        intent_map = {
            "constraint": "add_constraint",
            "conflict": "explain_conflict",
            "suggestion": "suggest_modification",
            "query": "query_schedule",
            "general": "general"
        }
        
        for key, value in intent_map.items():
            if key in intent:
                return value
        
        return "general"
    
    async def _parse_constraint(self, message: str, language: str) -> Optional[Dict[str, Any]]:
        """Parse natural language constraint into structured format."""
        # Get entities from database for context
        teachers = self.db.query(Teacher).all()
        subjects = self.db.query(Subject).all()
        rooms = self.db.query(Room).all()
        classes = self.db.query(ClassGroup).all()
        
        context = {
            "teachers": [{"id": t.id, "name": t.full_name} for t in teachers],
            "subjects": [{"id": s.id, "name_he": s.name_he, "name_fr": s.name_fr} for s in subjects],
            "rooms": [{"id": r.id, "code": r.code, "name": r.name} for r in rooms],
            "classes": [{"id": c.id, "code": c.code, "name": c.name} for c in classes]
        }
        
        system_prompt = self._get_constraint_parsing_prompt(language, context)
        
        if settings.USE_CLAUDE:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.2,
                system=system_prompt,
                messages=[{"role": "user", "content": message}]
            )
            content = response.content[0].text
        else:
            response = self.client.ChatCompletion.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            content = response.choices[0].message.content
        
        try:
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError:
            logger.error(f"Failed to parse constraint JSON: {content}")
            return None
    
    async def _explain_conflicts(self, conflicts: List[Dict[str, Any]], language: str) -> str:
        """Explain scheduling conflicts in natural language."""
        if not conflicts:
            if language == "fr":
                return "Aucun conflit détecté dans l'emploi du temps."
            else:
                return "לא נמצאו התנגשויות בלוח הזמנים."
        
        # Load related entities for better explanation
        conflict_details = []
        for conflict in conflicts:
            if conflict.get("conflict_type") == "teacher_overlap":
                # Get teacher and class details
                details = self._get_teacher_conflict_details(conflict)
                conflict_details.append(details)
            elif conflict.get("conflict_type") == "room_overlap":
                details = self._get_room_conflict_details(conflict)
                conflict_details.append(details)
            else:
                conflict_details.append(conflict)
        
        system_prompt = self._get_conflict_explanation_prompt(language)
        conflicts_json = json.dumps(conflict_details, ensure_ascii=False)
        
        if settings.USE_CLAUDE:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": conflicts_json}]
            )
            return response.content[0].text
        else:
            response = self.client.ChatCompletion.create(
                model=self.model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": conflicts_json}
                ]
            )
            return response.choices[0].message.content
    
    async def _generate_suggestions(
        self, 
        schedule_data: Dict[str, Any], 
        language: str
    ) -> List[Dict[str, Any]]:
        """Generate suggestions to improve or fix the schedule."""
        # Analyze current schedule
        analysis = self._analyze_schedule(schedule_data)
        
        system_prompt = self._get_suggestion_prompt(language)
        analysis_json = json.dumps(analysis, ensure_ascii=False)
        
        if settings.USE_CLAUDE:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.4,
                system=system_prompt,
                messages=[{"role": "user", "content": analysis_json}]
            )
            content = response.content[0].text
        else:
            response = self.client.ChatCompletion.create(
                model=self.model,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": analysis_json}
                ]
            )
            content = response.choices[0].message.content
        
        try:
            suggestions = json.loads(content)
            return suggestions.get("suggestions", [])
        except json.JSONDecodeError:
            logger.error(f"Failed to parse suggestions JSON: {content}")
            return []
    
    async def _query_schedule(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]], 
        language: str
    ) -> Dict[str, Any]:
        """Answer queries about the schedule."""
        schedule_id = context.get("schedule_id") if context else None
        if not schedule_id:
            if language == "fr":
                return {
                    "response": "Aucun emploi du temps actif. Veuillez d'abord générer un emploi du temps."
                }
            else:
                return {
                    "response": "אין לוח זמנים פעיל. אנא צור לוח זמנים תחילה."
                }
        
        # Get schedule data
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            if language == "fr":
                return {"response": "Emploi du temps introuvable."}
            else:
                return {"response": "לוח הזמנים לא נמצא."}
        
        # Prepare context for query
        query_context = self._prepare_schedule_context(schedule)
        
        system_prompt = self._get_query_prompt(language)
        query_with_context = f"Context: {json.dumps(query_context, ensure_ascii=False)}\n\nQuery: {query}"
        
        if settings.USE_CLAUDE:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": query_with_context}]
            )
            answer = response.content[0].text
        else:
            response = self.client.ChatCompletion.create(
                model=self.model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_with_context}
                ]
            )
            answer = response.choices[0].message.content
        
        return {"response": answer}
    
    async def _generate_response(self, message: str, language: str) -> str:
        """Generate a general response."""
        system_prompt = self._get_general_system_prompt(language)
        
        # Include recent conversation history
        messages = []
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            if settings.USE_CLAUDE:
                messages.append({
                    "role": msg.role.value if msg.role != ConversationRole.SYSTEM else "user",
                    "content": msg.content
                })
            else:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        if settings.USE_CLAUDE:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=settings.AI_TEMPERATURE,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        else:
            messages.insert(0, {"role": "system", "content": system_prompt})
            response = self.client.ChatCompletion.create(
                model=self.model,
                temperature=settings.AI_TEMPERATURE,
                messages=messages
            )
            return response.choices[0].message.content
    
    def _generate_constraint_confirmation(
        self, 
        constraint: Dict[str, Any], 
        language: str
    ) -> str:
        """Generate confirmation message for added constraint."""
        if language == "fr":
            return f"J'ai bien compris. La contrainte suivante a été ajoutée : {json.dumps(constraint, ensure_ascii=False, indent=2)}"
        else:
            return f"הבנתי. האילוץ הבא נוסף: {json.dumps(constraint, ensure_ascii=False, indent=2)}"
    
    def _format_suggestions(self, suggestions: List[Dict[str, Any]], language: str) -> str:
        """Format suggestions for display."""
        if not suggestions:
            if language == "fr":
                return "Aucune suggestion disponible pour le moment."
            else:
                return "אין הצעות זמינות כרגע."
        
        if language == "fr":
            response = "Voici mes suggestions pour améliorer l'emploi du temps :\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                response += f"{i}. {suggestion.get('description', '')}\n"
                if suggestion.get('impact'):
                    response += f"   Impact : {suggestion['impact']}\n"
                response += "\n"
        else:
            response = "הנה ההצעות שלי לשיפור לוח הזמנים:\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                response += f"{i}. {suggestion.get('description', '')}\n"
                if suggestion.get('impact'):
                    response += f"   השפעה: {suggestion['impact']}\n"
                response += "\n"
        
        return response
    
    def _analyze_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze schedule for potential improvements."""
        analysis = {
            "total_lessons": len(schedule_data.get("entries", [])),
            "conflicts": schedule_data.get("conflicts", []),
            "teacher_loads": {},
            "class_distributions": {},
            "room_utilization": {},
            "issues": []
        }
        
        # Analyze teacher loads
        for entry in schedule_data.get("entries", []):
            teacher_id = entry.get("teacher_id")
            if teacher_id:
                if teacher_id not in analysis["teacher_loads"]:
                    analysis["teacher_loads"][teacher_id] = 0
                analysis["teacher_loads"][teacher_id] += 1
        
        # Identify overloaded teachers
        for teacher_id, load in analysis["teacher_loads"].items():
            teacher = self.db.query(Teacher).filter(Teacher.id == teacher_id).first()
            if teacher and load > teacher.max_hours_per_week:
                analysis["issues"].append({
                    "type": "teacher_overload",
                    "teacher_id": teacher_id,
                    "load": load,
                    "max": teacher.max_hours_per_week
                })
        
        return analysis
    
    def _prepare_schedule_context(self, schedule: Schedule) -> Dict[str, Any]:
        """Prepare schedule context for queries."""
        entries = []
        for entry in schedule.entries:
            entries.append({
                "day": entry.day_of_week,
                "period": entry.period,
                "class": entry.class_group.name,
                "subject": entry.subject.name_he,
                "teacher": entry.teacher.full_name,
                "room": entry.room.name
            })
        
        return {
            "schedule_name": schedule.name,
            "status": schedule.status,
            "entries_count": len(entries),
            "entries": entries[:20]  # Limit to prevent token overflow
        }
    
    def _get_teacher_conflict_details(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about teacher conflicts."""
        # Implementation would fetch actual teacher and class details
        return conflict
    
    def _get_room_conflict_details(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about room conflicts."""
        # Implementation would fetch actual room details
        return conflict
    
    # System prompts for different tasks
    def _get_intent_system_prompt(self, language: str) -> str:
        """Get system prompt for intent detection."""
        if language == "fr":
            return """
            Vous êtes un assistant pour déterminer l'intention de l'utilisateur.
            Répondez avec un seul mot parmi : constraint, conflict, suggestion, query, general
            
            - constraint : L'utilisateur veut ajouter une contrainte
            - conflict : L'utilisateur demande des explications sur des conflits
            - suggestion : L'utilisateur veut des suggestions d'amélioration
            - query : L'utilisateur pose une question sur l'emploi du temps
            - general : Conversation générale
            """
        else:
            return """
            אתה עוזר לזיהוי כוונת המשתמש.
            ענה במילה אחת מתוך: constraint, conflict, suggestion, query, general
            
            - constraint : המשתמש רוצה להוסיף אילוץ
            - conflict : המשתמש מבקש הסברים על התנגשויות
            - suggestion : המשתמש רוצה הצעות לשיפור
            - query : המשתמש שואל שאלה על לוח הזמנים
            - general : שיחה כללית
            """
    
    def _get_constraint_parsing_prompt(self, language: str, context: Dict[str, Any]) -> str:
        """Get system prompt for constraint parsing."""
        context_json = json.dumps(context, ensure_ascii=False)
        
        if language == "fr":
            return f"""
            Vous êtes un assistant expert pour analyser les contraintes d'emploi du temps scolaire.
            
            Contexte disponible :
            {context_json}
            
            Analysez le message de l'utilisateur et extrayez une contrainte structurée.
            Répondez UNIQUEMENT avec un JSON valide dans ce format :
            {{
                "entity_type": "teacher|class|room|global",
                "entity_id": null ou ID de l'entité,
                "constraint_type": "availability|preference|requirement",
                "parameters": {{
                    // Paramètres spécifiques à la contrainte
                }},
                "confidence": 0.0-1.0
            }}
            
            Exemples de paramètres :
            - Pour disponibilité : {{"day": 0-5, "start_time": "HH:MM", "end_time": "HH:MM", "available": true/false}}
            - Pour préférence : {{"preference_type": "no_early_monday", "weight": 1-10}}
            - Pour exigence : {{"hours_per_week": N, "max_per_day": N}}
            """
        else:
            return f"""
            אתה עוזר מומחה לניתוח אילוצי מערכת שעות.
            
            הקשר זמין:
            {context_json}
            
            נתח את הודעת המשתמש וחלץ אילוץ מובנה.
            ענה רק עם JSON תקין בפורמט הבא:
            {{
                "entity_type": "teacher|class|room|global",
                "entity_id": null או מזהה הישות,
                "constraint_type": "availability|preference|requirement",
                "parameters": {{
                    // פרמטרים ספציפיים לאילוץ
                }},
                "confidence": 0.0-1.0
            }}
            
            דוגמאות לפרמטרים:
            - לזמינות: {{"day": 0-5, "start_time": "HH:MM", "end_time": "HH:MM", "available": true/false}}
            - להעדפה: {{"preference_type": "no_early_monday", "weight": 1-10}}
            - לדרישה: {{"hours_per_week": N, "max_per_day": N}}
            """
    
    def _get_conflict_explanation_prompt(self, language: str) -> str:
        """Get system prompt for conflict explanation."""
        if language == "fr":
            return """
            Vous êtes un assistant expert en emploi du temps scolaire.
            Expliquez les conflits de manière claire et non technique.
            
            Pour chaque conflit :
            1. Décrivez le problème en termes simples
            2. Expliquez pourquoi c'est un problème
            3. Suggérez des solutions possibles
            
            Utilisez un langage accessible aux administrateurs scolaires.
            """
        else:
            return """
            אתה עוזר מומחה במערכות שעות בית ספר.
            הסבר את ההתנגשויות בצורה ברורה ולא טכנית.
            
            לכל התנגשות:
            1. תאר את הבעיה במילים פשוטות
            2. הסבר למה זו בעיה
            3. הצע פתרונות אפשריים
            
            השתמש בשפה נגישה למנהלי בתי ספר.
            """
    
    def _get_suggestion_prompt(self, language: str) -> str:
        """Get system prompt for generating suggestions."""
        if language == "fr":
            return """
            Vous êtes un expert en optimisation d'emplois du temps scolaires.
            
            Analysez les données fournies et générez des suggestions concrètes.
            Répondez avec un JSON :
            {{
                "suggestions": [
                    {{
                        "type": "constraint_relaxation|resource_addition|schedule_modification",
                        "description": "Description claire de la suggestion",
                        "impact": "Impact attendu",
                        "implementation": "Comment implémenter",
                        "priority": "high|medium|low"
                    }}
                ]
            }}
            
            Considérez les spécificités israéliennes :
            - Vendredi écourté
            - Séparation garçons/filles pour certains cours
            - Cours religieux
            """
        else:
            return """
            אתה מומחה באופטימיזציה של מערכות שעות.
            
            נתח את הנתונים וצור הצעות קונקרטיות.
            ענה עם JSON:
            {{
                "suggestions": [
                    {{
                        "type": "constraint_relaxation|resource_addition|schedule_modification",
                        "description": "תיאור ברור של ההצעה",
                        "impact": "ההשפעה הצפויה",
                        "implementation": "איך ליישם",
                        "priority": "high|medium|low"
                    }}
                ]
            }}
            
            קח בחשבון מאפיינים ישראליים:
            - יום שישי מקוצר
            - הפרדה בנים/בנות לשיעורים מסוימים
            - שיעורי דת
            """
    
    def _get_query_prompt(self, language: str) -> str:
        """Get system prompt for answering queries."""
        if language == "fr":
            return """
            Vous êtes un assistant pour répondre aux questions sur l'emploi du temps.
            
            Répondez de manière claire et concise.
            Si les données ne permettent pas de répondre, dites-le clairement.
            Utilisez les informations du contexte fourni.
            """
        else:
            return """
            אתה עוזר לענות על שאלות על לוח הזמנים.
            
            ענה בצורה ברורה ותמציתית.
            אם הנתונים לא מאפשרים לענות, אמור זאת בבירור.
            השתמש במידע מההקשר שסופק.
            """
    
    def _get_general_system_prompt(self, language: str) -> str:
        """Get general system prompt."""
        if language == "fr":
            return """
            Vous êtes un assistant IA expert en gestion d'emplois du temps scolaires.
            Vous aidez les administrateurs d'écoles israéliennes à créer et optimiser leurs emplois du temps.
            
            Vos capacités :
            - Comprendre et formaliser des contraintes en langage naturel
            - Expliquer les conflits de manière non technique
            - Suggérer des améliorations
            - Répondre aux questions sur les emplois du temps
            
            Soyez professionnel, clair et aidant.
            """
        else:
            return """
            אתה עוזר AI מומחה בניהול מערכות שעות בית ספר.
            אתה עוזר למנהלי בתי ספר בישראל ליצור ולייעל את מערכות השעות שלהם.
            
            היכולות שלך:
            - להבין ולפרמל אילוצים בשפה טבעית
            - להסביר התנגשויות בצורה לא טכנית
            - להציע שיפורים
            - לענות על שאלות על מערכות השעות
            
            היה מקצועי, ברור ועוזר.
            """ 