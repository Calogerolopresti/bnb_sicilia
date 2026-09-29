from datetime import date, timedelta
from flask import Flask, render_template, redirect, url_for, flash, abort
import database

app = Flask(__name__)
app.secret_key = "bnb_sicilia_secret_key_super_sicura"

# ==============================================================================
# COSTANTI E WHITELIST
# ==============================================================================
STATI_CAMERA = ['libera', 'occupata', 'pulizia']
STATI_SOGGIORNO = ['prenotato', 'check_in', 'check_out', 'annullato']

CATALOGO_EXTRA = {
    1: ("Tour dell'Etna", 65.00),
    2: ("Degustazione vini etnei", 35.00),
    3: ("Transfer aeroporto Catania", 45.00),
    4: ("Colazione siciliana in terrazza", 12.00),
    5: ("Cooking class arancine e cannoli", 50.00),
}


# ==============================================================================
# PAGINA 1: DASHBOARD (index.html)
# ==============================================================================
@app.route("/")
def index():
    camere_stato = database.conta_camere_per_stato()
    arrivi = database.lista_arrivi_oggi()
    partenze = database.lista_partenze_oggi()

    # Organizziamo i contatori per la vista
    totali = {'libera': 0, 'occupata': 0, 'pulizia': 0}
    for item in camere_stato:
        totali[item['stato']] = item['totale']

    return render_template("index.html", totali=totali, arrivi=arrivi, partenze=partenze)


# ==============================================================================
# PAGINA 2: GESTIONE CAMERE (camere.html)
# ==============================================================================
@app.route("/camere")
def camere():
    lista_c = database.lista_camere()
    return render_template("camere.html", camere=lista_c)


@app.route("/camere/stato/<int:id_camera>/<stato>")
def camere_cambia_stato(id_camera, stato):
    if stato not in STATI_CAMERA:
        flash("Stato camera non valido!", "danger")
        return redirect(url_for("camere"))

    camera = database.get_camera(id_camera)
    if not camera:
        abort(404)

    database.aggiorna_stato_camera(id_camera, stato)
    flash(f"Stato della camera {camera['numero']} aggiornato in '{stato}'.", "success")
    return redirect(url_for("camere"))


# ==============================================================================
# PAGINA 3: NUOVA PRENOTAZIONE (prenota.html)
# ==============================================================================
@app.route("/prenota/<int:id_camera>")
def prenota(id_camera):
    camera = database.get_camera(id_camera)
    if not camera:
        abort(404)

    ospiti = database.lista_ospiti()
    data_oggi = date.today().strftime("%d/%m/%Y")
    return render_template("prenota.html", camera=camera, ospiti=ospiti, data_oggi=data_oggi)


@app.route("/conferma/<int:id_camera>/<int:id_ospite>/<int:notti>")
def conferma_prenotazione(id_camera, id_ospite, notti):
    if notti not in [1, 2, 3, 5, 7]:
        flash("Durata del soggiorno non valida!", "danger")
        return redirect(url_for("camere"))

    camera = database.get_camera(id_camera)
    ospite = database.get_ospite(id_ospite)
    if not camera or not ospite:
        abort(404)

    checkin = date.today()
    checkout = checkin + timedelta(days=notti)

    # Verifica disponibilità date
    if not database.camera_disponibile(id_camera, checkin, checkout):
        flash(f"La camera {camera['numero']} non è disponibile per le date selezionate!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    id_soggiorno = database.crea_soggiorno(id_camera, id_ospite, checkin, checkout)
    flash("Prenotazione creata con successo!", "success")
    return redirect(url_for("soggiorno_dettaglio", id_soggiorno=id_soggiorno))


# ==============================================================================
# PAGINA 4: LISTA SOGGIORNI (soggiorni.html)
# ==============================================================================
@app.route("/soggiorni")
def soggiorni():
    lista_s = database.lista_soggiorni()
    return render_template("soggiorni.html", soggiorni=lista_s)


@app.route("/soggiorni/stato/<int:id_soggiorno>/<stato>")
def soggiorno_cambia_stato(id_soggiorno, stato):
    if stato not in STATI_SOGGIORNO:
        flash("Stato soggiorno non valido!", "danger")
        return redirect(url_for("soggiorni"))

    soggiorno = database.get_soggiorno(id_soggiorno)
    if not soggiorno:
        abort(404)

    database.aggiorna_stato_soggiorno(id_soggiorno, stato)

    # Aggiornamento automatico dello stato della camera in base al soggiorno
    if stato == 'check_in':
        database.aggiorna_stato_camera(soggiorno['id_camera'], 'occupata')
    elif stato == 'check_out':
        database.aggiorna_stato_camera(soggiorno['id_camera'], 'pulizia')
    elif stato == 'annullato':
        database.aggiorna_stato_camera(soggiorno['id_camera'], 'libera')

    flash(f"Soggiorno aggiornato allo stato '{stato}'.", "success")
    return redirect(url_for("soggiorni"))


# ==============================================================================
# PAGINA 5: DETTAGLIO SOGGIORNO ED EXTRA (soggiorno.html)
# ==============================================================================
@app.route("/soggiorno/<int:id_soggiorno>")
def soggiorno_dettaglio(id_soggiorno):
    soggiorno = database.get_soggiorno(id_soggiorno)
    if not soggiorno:
        abort(404)

    extra_lista = database.lista_extra_soggiorno(id_soggiorno)
    tot_extra = database.totale_extra(id_soggiorno)

    # Calcolo totale notti e totale soggiorno
    notti = (soggiorno['data_checkout'] - soggiorno['data_checkin']).days
    totale_camere = notti * soggiorno['prezzo_notte']
    conto_totale = totale_camere + tot_extra

    return render_template("soggiorno.html",
                           soggiorno=soggiorno,
                           extra_lista=extra_lista,
                           tot_extra=tot_extra,
                           notti=notti,
                           totale_camere=totale_camere,
                           conto_totale=conto_totale,
                           catalogo=CATALOGO_EXTRA)


@app.route("/soggiorno/<int:id_soggiorno>/extra/<int:codice>")
def aggiungi_extra_soggiorno(id_soggiorno, codice):
    if codice not in CATALOGO_EXTRA:
        flash("Servizio extra non presente nel catalogo!", "danger")
        return redirect(url_for("soggiorno_dettaglio", id_soggiorno=id_soggiorno))

    soggiorno = database.get_soggiorno(id_soggiorno)
    if not soggiorno:
        abort(404)

    nome_servizio, prezzo = CATALOGO_EXTRA[codice]
    database.aggiungi_extra(id_soggiorno, nome_servizio, prezzo, date.today())
    flash(f"Servizio '{nome_servizio}' aggiunto al conto!", "success")
    return redirect(url_for("soggiorno_dettaglio", id_soggiorno=id_soggiorno))


@app.route("/extra/rimuovi/<int:id_extra>/<int:id_soggiorno>")
def rimuovi_extra_soggiorno(id_extra, id_soggiorno):
    database.rimuovi_extra(id_extra)
    flash("Servizio extra rimosso con successo.", "warning")
    return redirect(url_for("soggiorno_dettaglio", id_soggiorno=id_soggiorno))


if __name__ == "__main__":
    app.run(debug=True, port=5001)