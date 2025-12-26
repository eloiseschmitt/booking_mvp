<!-- Copilot / AI agent guidance for contributors working on booking_mvp -->
# Instructions AI pour contribuer au dépôt Booking MVP (fr)

Objectif rapide
- Aider un agent IA à devenir productif immédiatement : architecture, flux de données, conventions et commandes utiles.

Vue d'ensemble (big picture)
- Projet Django monorepo : app principales `accounts` (domain métier), `users` (user model), et le projet racine `booking_mvp`.
- Front minimal : templates dans `templates/accounts/` + JS centralisé dans `static/js/dashboard.js` pour toutes les interactions du tableau de bord.
- Base de données SQLite locale (voir `booking_mvp/settings.py`) ; `AUTH_USER_MODEL` = `users.User`.

Points architecture importants
- `accounts/planning.py` construit la vue semaine/jour : il renvoie soit des événements DB, soit un fallback sample week (fonction `_fallback_sample_week`) utilisé quand aucun calendrier n'existe.
- Le mapping entre titre d'événement et `Service` est résolu via `_build_service_lookup()` (voir `accounts/planning.py`).
- Logique métier liée aux formulaires Service centralisée dans `accounts/services.py` (préparation, sauvegarde, suppression).
- Templates fragmentés : `dashboard.html` charge `dashboard_services.html` et `dashboard_planning.html` (voir `templates/accounts/`).

Conventions spéciales du projet
- Aucun JS inline : tout le comportement est dans `static/js/dashboard.js`. Modifier ce fichier pour changements d'interactions UI.
- Les helpers métiers (préparation/sauvegarde) restent dans `accounts/services.py` et ne doivent pas être dupliqués dans les vues.
- Dates/heures : code utilise `django.utils.timezone` et renvoie des ISO strings pour le front (voir `_build_event_view`). Respecter les conversions timezone-aware.
- Respecter les bonnes pratiques de développement d'application web/Django:
  - Pas de nouvelle app « poubelle » du type core, utils sans justification solide.
  - La logique métier substantielle est dans des services / domain objects, pas dans :
    - Vues (views.py)
    - serializers
    - management commands
    - signaux
  - Les nouveaux modèles / champs :
    - suivent les conventions de nommage
    - ont des verbose_name / help_text utiles si exposés en admin
  - Les FK ont un on_delete explicite et cohérent
  - Les contraintes d’unicité / logique simple sont en base (UniqueConstraint, CheckConstraint) si possible
  - Les migrations :
    - sont atomiques et claires (une intention par migration)
    - n’embarquent pas de gros traitements métier / boucles sur toute la table
    - ne contiennent pas d’accès réseau ou de dépendance à des services externes
  - Pas de N+1 évident : select_related / prefetch_related utilisés quand il faut
  - Les filtres utilisent des champs indexés pour les gros volumes
  - Pas de requêtes dans des boucles Python alors qu’une requête agrégée est possible
  - Aucun raw() / SQL brut sans forte raison + commentaire expliquant pourquoi
  - Les views sont minces, elles parse la requête, appellent un service, et formatent la réponse
  - La validation technique (formats, champs obligatoires) est bien dans :
    - serializer / form / model validator,
    - et pas en vrac dans la view.
  - Pour les règles critiques : il existe au moins un test ciblé
  - L’accès aux views / endpoints sensibles est protégé :
    - auth obligatoire si nécessaire,
    - `permission_classes` / mixins adaptés, pas de « bricolage » à la main
  - Pas de données sensibles dans les réponses (logs ou JSON)
  - Pas de |safe dans les templates sans nécessité absolue + explication
  - Pas de secret / token / URL sensible en dur :
    - utilise les settings + variables d’env.
  - Si du téléchargement / upload de fichiers :
    - extensions / types sont vérifiés,
    - pas de risque évident d’exécution de fichier côté serveur.
  - Les tests sont lisibles :
    - nom parlant,
    - arrange / act / assert clair,
    - pas d’assertions trop magiques.
  - Les tests n’**appellent pas des services externes** :
    - mocks/fakes pour réseau, filesystems, etc
  - Pas de dépendance à l’ordre d’exécution ni à l’horloge réelle (si besoin : freezegun, etc.)
  - Pas de traitement lourd dans la requête HTTP :
    - si long ou massif → tâche Celery / job async
  - Les endpoints critiques ont au moins une réflexion perf (commentaire ou design clair) :
    - pagination,
    - filtres,
    - taille des réponses.
  - Pas de sleep / attente bloquante inutile
  - Si du cache est utilisé :
    - la stratégie d’invalidation est exprimée quelque part (code + commentaire / doc)
  - Les modifications d’admin :
    - ne donnent pas accès à des actions dangereuses aux mauvais rôles,
    - n’exposent pas de données sensibles en clair
  - Les `@admin.action` ont :
    - une confirmation,
    - une indication claire des effets
  - Les `management commands` :
    - loggent quelque chose d’utile,
    - ont un comportement raisonnable en cas d’erreur (exit code, messages),
    - peuvent tourner sans interaction manuelle.
  - Nommage des variables / fonctions explicite, pas de magie inutile
  - Pas de duplication évidente : si un pattern revient, on se pose la question de l’extraire
  - Les commentaires expliquent le pourquoi, pas le ce que (déjà visible dans le code)
  - Aucun log de prod n’affiche des secrets ou payloads sensibles
  - Les erreurs critiques sont loggées de façon structurée (niveau, contexte, ID de corrélation si vous en avez un)

Workflows développeur et commandes utiles
- Dev server : `python manage.py migrate` puis `python manage.py runserver`.
- Tests unitaires Django (profilés dans CI) :
  - lancer les tests d'une app : `python manage.py test accounts`
  - avec couverture : `coverage run --source=accounts,booking_mvp,users manage.py test`
- Linters / typing : `ruff check .` et `mypy .` (pré-commit hooks actifs). Voir `README.md` pour les prérequis.
- Front tests : `npm install` puis `npm test` pour les tests Jest présents dans `static/js/__tests__/`.

Points d'intégration et CI
- CI exécute `ruff`, `mypy`, tests Python (coverage) et publie vers SonarCloud. Voir `.github/workflows/ci.yml`.
- Si vous modifiez la structure des modèles (migrations), ajoutez/synchronisez les migrations dans `accounts/migrations/`.

Exemples concrets et fichiers clés
- Planning fallback : `accounts/planning.py` (fonctions `_fallback_sample_week`, `build_calendar_events`).
- Services form helpers : `accounts/services.py` (`prepare_service_form`, `save_service_form`).
- Templates fragments UI : `templates/accounts/dashboard_services.html`, `templates/accounts/dashboard_planning.html`.
- JS central : `static/js/dashboard.js` (contrôles des modales et navigation jour/semaine).

Comment demander de l'aide à l'IA
- Si vous demandez des changements UI/JS, fournissez la portion de template/JS et l'URL d'exemple (ex : dashboard, vue semaine). Indiquez le comportement attendu et la vue actuelle.
- Pour des changements métier (planning / services), fournissez les tests failing (si existants) et la partie de `accounts/planning.py` ou `accounts/services.py` concernée.
- Avant toute PR générée par l'IA, demandez explicitement : "exécuter les tests unitaires locaux et linters ?" pour valider.

Limites connues
- Projet conçu comme prototype (DEBUG=True, clé secrète en clair). Ne pas promouvoir ces valeurs en production.

Notes de maintenance
- Garder les helpers métiers dans `accounts/` et éviter d'introduire logique utilisateur directement dans les templates.

Merci — donnez un retour si certaines sections sont manquantes ou trop vagues.
