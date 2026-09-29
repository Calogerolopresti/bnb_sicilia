# 📋 Istruzioni e Vincoli Tecnici per Antigravity IDE

Sei il co-pilota di sviluppo per un progetto scolastico/universitario sviluppato in Python con Flask e MySQL. 
Devi rispettare tassativamente tutti i vincoli descritti in questo documento per evitare penalizzazioni o invalidazioni del progetto.

---

## 1. Regole Generali e Architettura

- **Stack Tecnologico:** Python (Flask) + MySQL + Bootstrap 5 (via CDN).
- **Niente ORM:** È **severamente vietato** l'uso di SQLAlchemy, Peewee o qualsiasi altro ORM. Tutte le query SQL devono essere scritte a mano in sintassi SQL pura all'interno del file `database.py`.
- **Niente Form HTML:** È **vietato** l'uso del tag `<form>` e di richieste POST per l'invio dati. 
  - La navigazione e l'esecuzione delle azioni avvengono **esclusivamente tramite link `<a>`** e parametri passati nell'URL (es. `/rotta/<int:id>`).
- **Gestione Pagine e Template:** 
  - Il sito deve essere composto da **esattamente 5 pagine HTML**.
  - Tutti i template HTML devono estendere `base.html` tramite ereditarietà Jinja2 (`{% extends "base.html" %}`).

---

## 2. Struttura Obbligatoria dei File

La struttura della cartella di progetto deve rimanere rigorosamente la seguente:

```text
progetto/
│
├── app.py              ← Le rotte/pagine del sito (una funzione per rotta)
├── database.py         ← Le query SQL (una funzione per query)
├── requirements.txt    ← Dipendenze (Flask, mysql-connector-python)
├── .gitignore          ← File e cartelle da ignorare su Git
├── README.md           ← Nomi del gruppo e descrizione del progetto
│
├── templates/          ← Contiene esattamente 6 file HTML
│   ├── base.html
│   ├── index.html
│   ├── pagina2.html
│   ├── pagina3.html
│   ├── pagina4.html
│   └── pagina5.html
│
└── static/
    └── style.css       ← Eventuali stili CSS personalizzati