# Token Tracker

Icône macOS dans la barre de menus qui affiche en temps réel le coût de vos sessions Claude Code.

![menu bar](https://img.shields.io/badge/macOS-menu%20bar-blue)

## Fonctionnalités

- **Coût du jour** affiché directement dans la barre de menus (`$0.42`)
- Suivi **aujourd'hui / semaine / mois** en USD
- **Barre de progression** du budget mensuel avec marqueur d'urgence visuel
- Détail par modèle (Opus, Sonnet, Haiku) avec tokens in/out/cache
- Budget configurable via un dialog natif
- Rafraîchissement automatique toutes les 2 minutes
- Démarrage automatique au login via LaunchAgent

## Prérequis

- macOS (Apple Silicon)
- Python 3.12 (`brew install python@3.12`)
- Claude Code installé (logs dans `~/.claude/projects/`)

## Installation

```bash
cd token-tracker
./install.sh
```

L'app démarre immédiatement et se relance à chaque login.

## Désinstallation

```bash
cd token-tracker
./uninstall.sh
```

## Tarifs utilisés

| Modèle | Input | Output | Cache write | Cache read |
|--------|-------|--------|-------------|------------|
| Opus   | $15 / M | $75 / M | $18.75 / M | $1.50 / M |
| Sonnet | $3 / M  | $15 / M | $3.75 / M  | $0.30 / M |
| Haiku  | $0.80 / M | $4 / M | $1 / M   | $0.08 / M |

## Architecture

```
token-tracker/
├── main.py                  # Point d'entrée
├── token_tracker/
│   ├── app.py               # App rumps (menu bar)
│   ├── log_parser.py        # Lecture des JSONL ~/.claude/projects/
│   └── pricing.py           # Calcul des coûts USD
├── install.sh               # Création venv + LaunchAgent
└── uninstall.sh             # Suppression propre
```

Les logs Claude Code (`~/.claude/projects/**/*.jsonl`) sont parsés localement — aucune donnée n'est envoyée à l'extérieur.
