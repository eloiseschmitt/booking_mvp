# Booking MVP

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=eloiseschmitt_booking_mvp&metric=coverage)](https://sonarcloud.io/summary/new_code?id=eloiseschmitt_booking_mvp)

Prototype Django qui combine gestion des prestations et pilotage d’un planning multi‑vues (semaine / jour) au sein d’un tableau de bord unique. L’objectif est d’offrir un socle minimal pour orchestrer catégories, services, rendez‑vous et synchroniser la qualité via une CI outillée (lint, typage, couverture, SonarCloud).

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation & exécution](#installation--exécution)
- [Qualité & automatisation](#qualité--automatisation)
- [Tests](#tests)
- [Structure du projet](#structure-du-projet)
- [Contribution](#contribution)

## Fonctionnalités

- **Tableau de bord unifié** : navigation entre les sections « prestations », « planning » et « clients » avec conservation de l’état courant via l’URL.
- **Gestion des prestations** :
  - création / édition de catégories et services via des modales dédiées ;
  - formulaires contextualisés (catégorie pré‑sélectionnée, ouverture automatique selon les paramètres GET) ;
  - listings stylés branchés sur les modèles `Category` et `Service`.
- **Planning avancé** :
  - vue semaine par défaut avec colonnes dynamiques, passage en vue jour ou aujourd’hui ;
  - navigation jour/semaine : les chevrons font défiler les jours en vue jour et les semaines en vue semaine ;
  - clic sur un créneau vide → modale « Créer un rendez-vous » pré‑remplie (date/heure) ;
  - sélection d’une prestation dans la liste des services appartenant à l’utilisateur connecté ;
  - clic sur un événement → modale détaillant date, horaire, service, catégorie, description, statut, auteur + bouton de suppression (hooké au niveau JS).
- **Données de secours** : si un calendrier est vide ou absent, `accounts.planning` génère automatiquement une semaine fallback lisible, recalculée pour la semaine actuellement affichée.
- **Front modulable** :
  - extraction des fragments `dashboard_services.html` et `dashboard_planning.html` pour alléger `dashboard.html` ;
  - JavaScript centralisé dans `static/js/dashboard.js`, aucun code inline ;
  - CSS située dans `static/css/dashboard.css`.

## Prérequis

- Python 3.11+
- Pip / virtualenv
- Base SQLite embarquée (aucune configuration particulière)
- SonarCloud (facultatif, mais déjà paramétré côté CI)

## Installation & exécution

```bash
git clone https://github.com/<votre-compte>/booking_mvp.git
cd booking_mvp
python -m venv .venv
source .venv/bin/activate  # ou .\.venv\Scripts\activate sur Windows
pip install --upgrade pip
pip install django==5.2.6 coverage ruff mypy black==23.9.1 pylint pre-commit
```

Initialiser la base puis lancer le serveur :

```bash
python manage.py migrate
python manage.py runserver
```

Le tableau de bord est accessible sur `http://127.0.0.1:8000/`.

## Qualité & automatisation

- **Ruff** : `ruff check .`
- **Black** : `black .` (la CI vérifie via `black --check .`)
- **Mypy** : `mypy .`
- **Pylint** : `pylint accounts booking_mvp users` (pensez à exporter `DJANGO_SETTINGS_MODULE=booking_mvp.settings`)
- **Pré-commit** : installez les hooks (Black, mypy, pylint) avec `pre-commit install` une fois l’environnement configuré.
- **CI GitHub Actions** (`.github/workflows/ci.yml`) :
  - lint + analyse statique (Ruff, Black, mypy, Pylint) ;
  - exécution des tests unitaires avec `coverage run` puis génération de `coverage.xml` ;
  - job SonarQube dédié (macOS) qui rejoue la suite de tests et pousse les rapports (badge de couverture ci‑dessus).

## Tests

```bash
python manage.py test accounts
# ou avec couverture
coverage run --source=accounts,booking_mvp,users manage.py test
coverage xml -o coverage.xml

# tests front (Jest) – lancés aussi en CI
npm install
npm test
```

Les tests couvrent notamment :

- la logique de layout du planning (`accounts/tests/test_planning.py`) ;
- les vues dashboard/services (`accounts/tests/test_views.py`) ;
- les scénarios sur les services/planning (autres fichiers dans `accounts/tests/`).

## Structure du projet

```
accounts/
  models.py          # Category, Service, Calendar, Event, ...
  planning.py        # Construction des vues semaine/jour + fallback
  services.py        # Logique métier autour des formulaires Service
  tests/             # Jeux de tests unitaires dédiés (views, planning, services, etc.)
static/
  css/dashboard.css  # Styles du tableau de bord
  js/dashboard.js    # Comportement interactif (sections, modales, planning)
templates/
  accounts/dashboard.html              # Shell principal
  accounts/dashboard_services.html     # Fragment prestations
  accounts/dashboard_planning.html     # Fragment planning (modales incluses)
users/                                  # App dédiée aux utilisateurs personnalisés
.github/workflows/ci.yml                # Pipeline lint/tests/Sonar
```

## Contribution

1. Créez une branche (`git checkout -b feature/...`).
2. Activez les hooks `pre-commit install`.
3. Développez puis exécutez les linters/tests mentionnés plus haut.
4. Poussez la branche et ouvrez une Pull Request (la CI s’exécutera automatiquement).

Pour toute nouvelle fonctionnalité, pensez à :

- ajouter des tests unitaires ou d’intégration pertinents ;
- documenter les comportements utilisateurs visibles dans ce README si nécessaire ;
- garder `coverage.xml` à jour pour SonarCloud.

Bonne contribution !
