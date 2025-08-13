# Calcio Under/Over – MVP

MVP con FastAPI + Next.js che stima probabilità Under/Over 2.5 utilizzando un modello Poisson semplice e dati mock.

## Avvio
- Docker: `docker compose up --build`
- Manuale: vedi istruzioni in repository.

## Per passare a dati reali
Modifica `backend/data/loader.py` con chiamate alle API di tuo interesse e mantieni le funzioni `get_matches` e `get_history`.
