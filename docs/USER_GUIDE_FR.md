# 📚 Guide Utilisateur - École Emploi du Temps

Bienvenue dans le guide d'utilisation complet de l'application École Emploi du Temps. Ce guide vous accompagnera dans la découverte et l'utilisation de toutes les fonctionnalités de l'application.

## 📋 Table des Matières

- [Démarrage Rapide](#démarrage-rapide)
- [Interface Principale](#interface-principale)
- [Gestion des Matières](#gestion-des-matières)
- [Gestion des Classes](#gestion-des-classes)
- [Gestion des Salles](#gestion-des-salles)
- [Gestion des Enseignants](#gestion-des-enseignants)
- [Génération d'Emplois du Temps](#génération-demplois-du-temps)
- [Personnalisation et Préférences](#personnalisation-et-préférences)
- [Export et Impression](#export-et-impression)
- [Conseils et Astuces](#conseils-et-astuces)
- [FAQ](#faq)

## 🚀 Démarrage Rapide

### Première Connexion

1. **Accès à l'application**
   - Ouvrez votre navigateur web
   - Rendez-vous sur l'adresse fournie par votre administrateur
   - Vous arrivez sur la page de connexion

2. **Connexion**
   - Saisissez votre email et mot de passe
   - Cliquez sur "Se connecter"
   - Si c'est votre première connexion, vous serez invité à changer votre mot de passe

3. **Interface de bienvenue**
   - Familiarisez-vous avec le tableau de bord
   - Consultez les widgets d'information
   - Explorez le menu de navigation

### Navigation Rapide

| Raccourci | Action |
|-----------|--------|
| `Ctrl + H` | Retour au tableau de bord |
| `Ctrl + N` | Nouveau (selon la page) |
| `Ctrl + S` | Sauvegarder |
| `Échap` | Fermer les modales |
| `F1` | Aide contextuelle |

## 🖥️ Interface Principale

### Tableau de Bord

Le tableau de bord est votre point central d'information :

#### Widgets Disponibles

1. **Statistiques Générales**
   - Nombre total de matières
   - Classes configurées
   - Salles disponibles
   - Enseignants actifs

2. **Activité Récente**
   - Dernières modifications
   - Emplois du temps générés
   - Actions utilisateurs

3. **Alertes et Notifications**
   - Conflits détectés
   - Tâches en attente
   - Mises à jour système

4. **Raccourcis Rapides**
   - Génération rapide d'emploi du temps
   - Accès aux modules principaux
   - Outils d'administration

### Menu de Navigation

Le menu latéral vous donne accès à tous les modules :

- **📊 Tableau de bord** : Vue d'ensemble
- **📚 Matières** : Gestion des disciplines
- **🏫 Classes** : Organisation des groupes d'élèves
- **🚪 Salles** : Gestion des espaces
- **👩‍🏫 Enseignants** : Profils des professeurs
- **📅 Emplois du Temps** : Planification et génération
- **⚙️ Paramètres** : Configuration personnelle
- **📋 Rapports** : Analyses et statistiques

### Barre d'Outils

En haut de l'interface :

- **🔍 Recherche globale** : Trouvez rapidement n'importe quel élément
- **🌐 Langue** : Basculer entre français et hébreu
- **🔔 Notifications** : Alertes en temps réel
- **👤 Profil** : Paramètres utilisateur et déconnexion

## 📚 Gestion des Matières

### Vue d'Ensemble

La section Matières vous permet de :
- Créer et modifier des disciplines
- Définir les niveaux requis
- Configurer les heures hebdomadaires
- Gérer les descriptions bilingues

### Créer une Nouvelle Matière

1. **Accéder au module**
   - Cliquez sur "Matières" dans le menu
   - Cliquez sur "+ Nouvelle Matière"

2. **Informations de base**
   ```
   Nom français : Mathématiques
   Nom hébreu : מתמטיקה
   Code : MATH
   ```

3. **Configuration pédagogique**
   - **Niveau requis** : Sélectionnez de 1 à 12
   - **Heures/semaine** : Entre 1 et 40 heures
   - **Type de matière** :
     - Obligatoire : Pour toutes les classes du niveau
     - Optionnelle : Au choix des élèves
     - Spécialisée : Pour certaines filières

4. **Descriptions**
   - Ajoutez une description en français
   - Ajoutez une description en hébreu
   - Mentionnez les prérequis si nécessaire

### Fonctionnalités Avancées

#### Recherche et Filtres

- **Recherche textuelle** : Par nom ou code
- **Filtre par niveau** : 1ère, 2nde, Terminale, etc.
- **Filtre par type** : Obligatoire, Optionnelle, Spécialisée
- **Filtre par heures** : Plages horaires personnalisées

#### Actions en Lot

- Sélectionnez plusieurs matières avec les cases à cocher
- Actions disponibles :
  - Modification en lot des niveaux
  - Export en Excel/CSV
  - Duplication avec modifications
  - Suppression multiple (avec confirmation)

#### Statistiques des Matières

Accédez aux statistiques via l'onglet "Statistiques" :

- **Répartition par niveau** : Graphique circulaire
- **Répartition par type** : Histogramme
- **Distribution des heures** : Analyse des charges horaires
- **Matières les plus utilisées** : Classement par classes

### Validation et Contrôles

L'application effectue automatiquement plusieurs vérifications :

✅ **Validations automatiques :**
- Unicité des codes de matière
- Format alphanumérique des codes
- Heures comprises entre 1 et 40
- Noms bilingues obligatoires

❌ **Erreurs communes à éviter :**
- Codes trop courts (minimum 2 caractères)
- Heures nulles ou négatives
- Descriptions vides dans les deux langues
- Doublons de noms dans la même langue

## 🏫 Gestion des Classes

### Organisation des Classes

La gestion des classes vous permet de :
- Structurer les groupes d'élèves
- Définir les effectifs
- Associer les matières obligatoires
- Configurer les préférences horaires

### Créer une Nouvelle Classe

1. **Informations générales**
   ```
   Nom de la classe : 3ème A
   Niveau : 9 (équivalent 3ème)
   Effectif : 28 élèves
   ```

2. **Matières obligatoires**
   - Sélectionnez les matières du tronc commun
   - L'application filtre automatiquement par niveau
   - Ajoutez les heures spécifiques si différentes

3. **Préférences horaires**
   ```json
   {
     "debut_prefere": "08:00",
     "fin_prefere": "16:00",
     "pause_dejeuner": "12:00-13:00",
     "jours_reduits": ["vendredi"],
     "contraintes_speciales": []
   }
   ```

### Configuration Avancée

#### Types de Classes

- **Classes générales** : Cursus standard
- **Classes spécialisées** : Sections particulières
- **Classes à effectif réduit** : Soutien ou excellence
- **Classes multi-niveaux** : Cours regroupés

#### Gestion des Effectifs

L'application vous aide à :
- Vérifier la compatibilité avec les salles
- Alerter en cas de sureffectif
- Proposer des divisions de classe
- Optimiser les regroupements

#### Horaires Préférés

Configuration flexible des créneaux :

- **Plages horaires favorites** : Matin, après-midi
- **Jours spéciaux** : Vendredi raccourci
- **Contraintes religieuses** : Respect des traditions
- **Activités extra-scolaires** : Blocs à éviter

### Associations Matières-Classes

#### Attribution Automatique

L'application propose automatiquement :
- Matières obligatoires selon le niveau
- Heures recommandées par matière
- Répartition équilibrée dans la semaine

#### Attribution Manuelle

Pour plus de contrôle :
- Glissez-déposez les matières
- Ajustez les heures individuellement
- Définissez des contraintes spécifiques
- Créez des groupes de niveau

### Validation et Conflits

#### Contrôles Automatiques

- **Cohérence niveau-matières** : Vérification des prérequis
- **Charge horaire** : Respect des limites réglementaires
- **Disponibilité salles** : Capacité suffisante
- **Planning enseignants** : Éviter les conflits

#### Résolution de Conflits

Quand des conflits sont détectés :
1. L'application les signale clairement
2. Suggestions de résolution automatique
3. Options de modification manuelle
4. Validation finale avant sauvegarde

## 🚪 Gestion des Salles

### Types de Salles

L'application gère différents types d'espaces :

#### Salles Standard
- **Salles de classe** : Cours généraux
- **Amphithéâtres** : Grands groupes
- **Salles de réunion** : Personnel administratif

#### Salles Spécialisées
- **Laboratoires** : Sciences, informatique
- **Ateliers** : Travaux pratiques
- **Salles multimédias** : Équipements audiovisuels
- **Gymnases** : Éducation physique

### Configuration des Salles

#### Informations de Base

```
Nom de la salle : Labo Chimie 1
Capacité : 24 élèves
Type : Laboratoire
Bâtiment : Sciences (optionnel)
Étage : 2ème (optionnel)
```

#### Équipements Disponibles

Configuration JSON flexible :
```json
{
  "audiovisuel": {
    "videoprojecteur": true,
    "tableau_interactif": true,
    "systeme_audio": true
  },
  "informatique": {
    "ordinateurs": 12,
    "tablets": 0,
    "wifi": true,
    "prises_eleves": 24
  },
  "laboratoire": {
    "postes_travail": 12,
    "hotte_aspirante": 2,
    "point_eau": 6,
    "materiel_securite": true
  },
  "mobilier": {
    "tables_mobiles": true,
    "chaises_ajustables": false,
    "rangements": "armoires_verrouillables"
  }
}
```

#### Disponibilités

Gestion fine des créneaux :
```json
{
  "lundi": {
    "08:00-12:00": "disponible",
    "13:00-17:00": "disponible"
  },
  "mardi": {
    "08:00-10:00": "maintenance",
    "10:00-17:00": "disponible"
  },
  "mercredi": {
    "08:00-17:00": "disponible"
  },
  "jeudi": {
    "08:00-17:00": "disponible"
  },
  "vendredi": {
    "08:00-13:00": "disponible"
  }
}
```

### Fonctionnalités Avancées

#### Recherche Intelligente

Trouvez rapidement la salle idéale :
- **Par capacité** : Minimum X élèves
- **Par équipements** : Vidéoprojecteur requis
- **Par disponibilité** : Créneau spécifique
- **Par proximité** : Même bâtiment/étage

#### Optimisation d'Utilisation

L'application analyse :
- **Taux d'occupation** : Pourcentage d'utilisation
- **Pic d'utilisation** : Heures de forte demande
- **Salles sous-utilisées** : Optimisation possible
- **Conflits potentiels** : Prévention des doubles réservations

#### Maintenance et Indisponibilités

Gestion des interruptions :
- **Maintenance programmée** : Créneaux bloqués
- **Pannes équipement** : Indisponibilité temporaire
- **Événements spéciaux** : Réservations exceptionnelles
- **Nettoyage approfondi** : Périodes dédiées

### Compatibilité Matières-Salles

#### Associations Automatiques

L'application suggère :
- **Sciences** → Laboratoires équipés
- **Informatique** → Salles avec ordinateurs
- **EPS** → Gymnases et terrains
- **Arts** → Ateliers spécialisés

#### Contraintes Personnalisées

Définissez vos propres règles :
- Matière X uniquement en salle Y
- Éviter certaines associations
- Préférences par enseignant
- Contraintes de sécurité

## 👩‍🏫 Gestion des Enseignants

### Profils Enseignants

#### Informations Personnelles

```
Nom : Dupont
Prénom : Marie
Email : marie.dupont@ecole.fr
Téléphone : +33 1 23 45 67 89
Statut : Titulaire
```

#### Qualifications et Spécialisations

- **Matières enseignées** : Liste des disciplines
- **Niveaux autorisés** : De la 6ème à la Terminale
- **Certifications** : CAPES, Agrégation, etc.
- **Formations continues** : Spécialisations récentes

#### Contraintes Horaires

Configuration flexible des disponibilités :

```json
{
  "temps_plein": true,
  "heures_max_semaine": 18,
  "jours_indisponibles": [],
  "creneaux_preferes": {
    "matin": true,
    "apres_midi": true,
    "en_soiree": false
  },
  "contraintes_personnelles": {
    "pause_dejeuner_min": 60,
    "cours_consecutifs_max": 4,
    "jours_travailles_max": 5
  }
}
```

### Gestion des Emplois du Temps

#### Charge de Travail

Suivi automatique :
- **Heures actuelles** : Décompte en temps réel
- **Heures restantes** : Capacité disponible
- **Répartition hebdomadaire** : Équilibrage des jours
- **Surcharge détectée** : Alertes automatiques

#### Préférences Pédagogiques

- **Salles préférées** : Espaces familiers
- **Créneaux optimaux** : Heures de prédilection
- **Groupes préférés** : Affinités avec certaines classes
- **Contraintes de déplacement** : Minimiser les changements

### Collaboration et Communication

#### Coordination Équipe

- **Équipes pédagogiques** : Regroupement par matière
- **Projets interdisciplinaires** : Coordination des cours
- **Remplacements** : Gestion des absences
- **Réunions d'équipe** : Créneaux communs

#### Notifications

Système d'alertes personnalisé :
- **Modifications emploi du temps** : Changements impactants
- **Conflits détectés** : Résolution nécessaire
- **Nouvelles affectations** : Classes ou salles
- **Rappels importants** : Réunions, formations

## 📅 Génération d'Emplois du Temps

### Assistant de Génération

L'outil de génération automatique est le cœur de l'application.

#### Préparation

Avant de lancer la génération :

1. **Vérification des données**
   - ✅ Toutes les matières sont configurées
   - ✅ Classes avec effectifs et matières
   - ✅ Salles avec capacités et équipements
   - ✅ Enseignants avec contraintes

2. **Paramètres de génération**
   ```
   Période : Année scolaire 2024-2025
   Semaines : 36 semaines de cours
   Jours : Lundi à Vendredi
   Créneaux : 8h00-17h00 par défaut
   ```

#### Lancement de la Génération

1. **Accéder à l'assistant**
   - Menu "Emplois du Temps"
   - Bouton "Nouvelle Génération"

2. **Sélection du périmètre**
   - Toutes les classes ou sélection
   - Période spécifique
   - Contraintes particulières

3. **Options avancées**
   - Priorité équilibrage/optimisation
   - Respect strict des préférences
   - Autoriser les créneaux flexibles

#### Algorithme d'Optimisation

L'application utilise un solveur avancé qui :

**Contraintes dures (obligatoires) :**
- Pas de conflit enseignant/salle/classe
- Respect des heures par matière
- Capacité des salles suffisante
- Disponibilités enseignants

**Contraintes souples (optimisations) :**
- Minimiser les trous dans les emplois
- Respecter les préférences horaires
- Équilibrer la charge quotidienne
- Éviter les déplacements inutiles

### Résolution des Conflits

#### Types de Conflits

1. **Conflits de ressources**
   - Enseignant sur plusieurs cours simultanés
   - Salle double-réservée
   - Classe en deux endroits

2. **Contraintes non respectées**
   - Heures insuffisantes pour une matière
   - Surcharge d'un enseignant
   - Incompatibilité salle-matière

#### Outils de Résolution

**Mode automatique :**
- Suggestions de modifications
- Réallocation intelligente
- Optimisation par permutations

**Mode manuel :**
- Éditeur glisser-déposer
- Vue calendrier interactive
- Modification créneau par créneau

### Validation et Optimisation

#### Critères de Qualité

L'application évalue automatiquement :

- **Score de satisfaction** : 0-100%
- **Taux de respect des préférences** : Contraintes souples
- **Équilibrage** : Répartition uniforme
- **Efficacité** : Minimisation des temps morts

#### Analyse Post-Génération

Rapports détaillés :
- Statistiques par classe/enseignant
- Identification des points d'amélioration
- Suggestions d'optimisation
- Comparaison avec versions précédentes

### Versions et Historique

#### Gestion des Versions

- **Sauvegarde automatique** : Chaque génération
- **Nommage intelligent** : Date et description
- **Comparaison visuelle** : Diff entre versions
- **Restauration rapide** : Retour en arrière

#### Collaboration

- **Commentaires** : Notes sur les modifications
- **Approbations** : Workflow de validation
- **Partage** : Accès contrôlé par rôle
- **Notifications** : Changements importants

## ⚙️ Personnalisation et Préférences

### Paramètres Utilisateur

#### Interface et Affichage

```
Langue : Français / עברית
Thème : Clair / Sombre / Auto
Fuseau horaire : Europe/Paris
Format de date : JJ/MM/AAAA
```

#### Notifications

Configuration fine des alertes :
- **Email** : Résumés quotidiens/hebdomadaires
- **Push** : Alertes temps réel
- **Seuils** : Personnalisation des déclencheurs
- **Canaux** : Slack, Teams, etc.

#### Dashboard Personnalisé

Organisez vos widgets :
- Glissez-déposez les éléments
- Redimensionnement libre
- Ajout/suppression de widgets
- Sauvegarde des layouts

### Préférences Institutionnelles

#### Calendrier Scolaire

Configuration spécifique à votre établissement :
```json
{
  "rentree": "2024-09-02",
  "vacances_toussaint": {
    "debut": "2024-10-21",
    "fin": "2024-11-04"
  },
  "vacances_noel": {
    "debut": "2024-12-23",
    "fin": "2025-01-06"
  },
  "fetes_religieuses": [
    "2024-10-07", // Rosh Hashana
    "2024-10-16", // Yom Kippour
    "2024-12-25"  // Noël
  ]
}
```

#### Règles Métier

Personnalisation des contraintes :
- **Heures max/jour** : Par niveau de classe
- **Pauses obligatoires** : Durées minimales
- **Cours consécutifs** : Limites par matière
- **Journées types** : Modèles prédéfinis

### Intégrations

#### Systèmes Externes

Connectez l'application à :
- **SIS** : Système d'information scolaire
- **Active Directory** : Authentification unique
- **Calendriers** : Outlook, Google Calendar
- **Communication** : Slack, Teams

#### APIs et Webhooks

Pour les développeurs :
- **API REST** : Accès programmatique
- **Webhooks** : Notifications automatiques
- **Export/Import** : Formats standards
- **Plugins** : Extensions personnalisées

## 📄 Export et Impression

### Formats d'Export

#### Emplois du Temps

**PDF :**
- Format A4 ou A3
- Portrait ou paysage
- Couleurs ou noir et blanc
- Multiple classes par page

**Excel/CSV :**
- Format structuré pour analyse
- Données brutes pour traitement
- Imports dans autres systèmes

**Calendriers :**
- Format ICS (Outlook, Google)
- Format JSON pour applications
- Synchronisation automatique

#### Types de Vues

1. **Vue par classe**
   - Emploi du temps d'une classe
   - Détails par créneau
   - Enseignants et salles

2. **Vue par enseignant**
   - Planning personnel
   - Charges horaires
   - Déplacements optimisés

3. **Vue par salle**
   - Occupation des espaces
   - Taux d'utilisation
   - Planning maintenance

4. **Vue globale**
   - Synthèse établissement
   - Statistiques générales
   - Indicateurs de performance

### Options d'Impression

#### Personnalisation

```
En-tête : Logo et nom établissement
Période : Semaine/Mois/Trimestre
Détails : Codes matières/Noms complets
Couleurs : Par matière/Par enseignant
```

#### Formats Prédéfinis

- **Affichage classe** : A4 portrait, grand format
- **Planning enseignant** : A4 paysage, compact
- **Tableau synthèse** : A3 paysage, vue d'ensemble
- **Planning élève** : Format poche, personnalisé

### Distribution et Partage

#### Diffusion Automatique

- **Email automatique** : Envoi programmé
- **Publication web** : Accès contrôlé
- **Impression en lot** : Tous les formats
- **Mise à jour dynamique** : Synchronisation temps réel

#### Contrôle d'Accès

- **Par rôle** : Enseignant, Administrateur, Élève
- **Par contenu** : Données personnelles seulement
- **Par période** : Accès temporaire
- **Audit** : Traçabilité des consultations

## 💡 Conseils et Astuces

### Optimisation des Performances

#### Génération Plus Rapide

1. **Préparez vos données**
   - Données complètes dès le départ
   - Contraintes réalistes uniquement
   - Préférences hiérarchisées

2. **Stratégie progressive**
   - Commencez par les classes complexes
   - Ajustez ensuite les détails
   - Validez étape par étape

#### Qualité des Résultats

**Bonnes pratiques :**
- Définissez des contraintes réalistes
- Priorisez les contraintes importantes
- Laissez de la flexibilité au système
- Testez différents paramètres

**À éviter :**
- Contraintes contradictoires
- Sur-contraindre le système
- Négliger les préférences enseignants
- Ignorer les retours utilisateurs

### Gestion du Changement

#### Planning de Déploiement

1. **Phase 1** : Formation équipe administrative
2. **Phase 2** : Test avec quelques classes
3. **Phase 3** : Déploiement progressif
4. **Phase 4** : Formation générale

#### Communication

- **Démonstrations** : Sessions découverte
- **Documentation** : Guides spécifiques par rôle
- **Support** : Assistance personnalisée
- **Feedback** : Collecte des suggestions

### Maintenance Préventive

#### Nettoyage Régulier

- **Données obsolètes** : Suppression automatique
- **Emplois du temps archivés** : Organisation par année
- **Logs système** : Rotation automatique
- **Performances** : Monitoring continu

#### Sauvegardes

- **Automatiques** : Quotidiennes en production
- **Manuelles** : Avant changements majeurs
- **Tests de restauration** : Validation périodique
- **Stockage externe** : Sécurité maximale

## ❓ FAQ

### Questions Générales

**Q : L'application fonctionne-t-elle hors ligne ?**
R : L'application nécessite une connexion internet pour la synchronisation, mais certaines fonctionnalités de consultation sont disponibles en mode hors ligne.

**Q : Puis-je modifier un emploi du temps déjà généré ?**
R : Oui, vous pouvez modifier manuellement chaque créneau. L'application vérifiera automatiquement les conflits.

**Q : Comment basculer entre français et hébreu ?**
R : Utilisez le sélecteur de langue en haut à droite de l'interface. Le changement est immédiat.

### Questions Techniques

**Q : Quel navigateur utiliser ?**
R : L'application est optimisée pour Chrome, Firefox, Safari et Edge récents. Évitez Internet Explorer.

**Q : L'application est-elle accessible sur mobile ?**
R : Oui, l'interface est responsive et s'adapte aux tablettes et smartphones.

**Q : Puis-je importer des données existantes ?**
R : Oui, l'application supporte l'import Excel/CSV. Contactez votre administrateur pour l'assistance.

### Résolution de Problèmes

**Q : Que faire si la génération échoue ?**
R : 
1. Vérifiez que toutes les données sont complètes
2. Réduisez les contraintes si nécessaire
3. Contactez le support avec le message d'erreur

**Q : Comment signaler un bug ?**
R : Utilisez le bouton "Signaler un problème" dans le menu d'aide, ou contactez support@ecole-emploidutemps.fr

**Q : Mes modifications ne sont pas sauvegardées**
R : Vérifiez votre connexion internet et les permissions. L'application affiche une confirmation à chaque sauvegarde.

### Support et Formation

**Q : Où trouver plus de documentation ?**
R : 
- Guide administrateur : [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
- Tutoriels vidéo : [VIDEO_TUTORIALS.md](VIDEO_TUTORIALS.md)
- API Documentation : [API_DOCS.md](API_DOCS.md)

**Q : Comment obtenir une formation ?**
R : Contactez votre administrateur système ou notre équipe support pour organiser une session de formation personnalisée.

---

📞 **Support** : support@ecole-emploidutemps.fr  
📚 **Documentation** : https://docs.ecole-emploidutemps.fr  
🎥 **Tutoriels** : https://videos.ecole-emploidutemps.fr

*Dernière mise à jour : v1.0.0 - Mars 2024* 