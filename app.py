from flask import Flask, render_template, redirect, url_for, flash
import database

app = Flask(__name__)
# Chiave segreta necessaria per la gestione dei messaggi flash e delle sessioni
app.secret_key = "Chiave26"

# ==============================================================================
# COSTANTI E WHITELIST (Sicurezza e dati fissi)
# ==============================================================================
STATI_CAMERA = ['libera', 'occupata', 'pulizia']
STATI_SOGGIORNO = ['prenotato', 'check_in', 'check_out', 'annullato']

# Catalogo fisso dei servizi extra acquistabili (senza form)
CATALOGO_EXTRA = {
    1: ("Tour dell'Etna", 65.00),
    2: ("Degustazione vini etnei", 35.00),
    3: ("Transfer aeroporto Catania", 45.00),
    4: ("Colazione siciliana in terrazza", 12.00),
    5: ("Cooking class arancine e cannoli", 50.00),
}


# ==============================================================================
# ROTTA TEMPORANEA DI TEST
# ==============================================================================
@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # Avvia il server Flask in modalità debug
    app.run(debug=True, port=5001)