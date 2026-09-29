import re
from datetime import date, timedelta
from flask import Flask, render_template, redirect, url_for, flash, abort, request
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

    # RISOLUZIONE PROBLEMA:
    # Non è possibile impostare la camera come 'occupata' se nessun ospite l'ha prenotata per oggi.
    if stato == 'occupata':
        soggiorno = database.get_soggiorno_oggi_camera(id_camera)
        if not soggiorno:
            flash(f"Impossibile impostare la camera {camera['numero']} come occupata: non risulta alcuna prenotazione per oggi!", "warning")
            return redirect(url_for("camere"))

        # Se la prenotazione per oggi era ancora solo 'prenotato', la portiamo a 'check_in'
        if soggiorno['stato'] == 'prenotato':
            database.aggiorna_stato_soggiorno(soggiorno['id_soggiorno'], 'check_in')

    # Aggiorna lo stato della camera
    database.aggiorna_stato_camera(id_camera, stato)

    # Se la camera viene liberata manualmente, annulliamo eventuali soggiorni
    # attivi ('prenotato' o 'check_in') associati per sbloccare le date nel DB.
    if stato == 'libera':
        database.annulla_soggiorni_camera(id_camera)

    flash(f"Stato della camera {camera['numero']} aggiornato in '{stato}'.", "success")
    return redirect(url_for("camere"))


# ==============================================================================
# PAGINA 3: NUOVA PRENOTAZIONE (prenota.html)
# ==============================================================================
@app.route("/prenota/<int:id_camera>", methods=["GET", "POST"])
def prenota(id_camera):
    camera = database.get_camera(id_camera)
    if not camera:
        abort(404)

    if request.method == "POST":
        id_ospite = request.form.get("id_ospite")
        checkin_str = request.form.get("checkin")
        checkout_str = request.form.get("checkout")

        if not id_ospite or not checkin_str or not checkout_str:
            flash("Compila tutti i campi obbligatori per completare la prenotazione!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        try:
            checkin = date.fromisoformat(checkin_str)
            checkout = date.fromisoformat(checkout_str)
        except ValueError:
            flash("Formato data non valido!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        # Controllo che le date non siano nel passato
        if checkin < date.today():
            flash("Non è possibile prenotare per date passate! Il check-in deve essere oggi o una data futura.", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        if checkout <= checkin:
            flash("La data di check-out deve essere successiva alla data di check-in!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        ospite = database.get_ospite(id_ospite)
        if not ospite:
            flash("Ospite non trovato!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        # Verifica disponibilità date nel database (impedisce doppie prenotazioni)
        if not database.camera_disponibile(id_camera, checkin, checkout):
            flash(f"La camera {camera['numero']} non è disponibile per le date selezionate ({checkin.strftime('%d/%m/%Y')} - {checkout.strftime('%d/%m/%Y')}): c'è già una prenotazione per quel periodo!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        # Se la prenotazione parte oggi e la camera risulta già occupata
        if checkin <= date.today() < checkout and camera['stato'] == 'occupata':
            flash(f"Impossibile completare la prenotazione: la camera {camera['numero']} risulta attualmente già occupata!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        id_soggiorno = database.crea_soggiorno(id_camera, id_ospite, checkin, checkout)

        # Se il soggiorno include la data odierna, aggiorniamo subito lo stato della camera a 'occupata'
        if checkin <= date.today() < checkout:
            database.aggiorna_stato_camera(id_camera, 'occupata')

        flash("Prenotazione creata con successo!", "success")
        return redirect(url_for("soggiorno_dettaglio", id_soggiorno=id_soggiorno))

    ospiti = database.lista_ospiti()
    prenotazioni_attive = database.lista_prenotazioni_camera(id_camera)
    data_oggi = date.today().strftime("%d/%m/%Y")
    data_oggi_iso = date.today().isoformat()
    data_domani_iso = (date.today() + timedelta(days=1)).isoformat()
    id_ospite_selezionato = request.args.get("id_ospite_selezionato", type=int)

    return render_template("prenota.html",
                           camera=camera,
                           ospiti=ospiti,
                           prenotazioni_attive=prenotazioni_attive,
                           data_oggi=data_oggi,
                           data_oggi_iso=data_oggi_iso,
                           data_domani_iso=data_domani_iso,
                           id_ospite_selezionato=id_ospite_selezionato)


@app.route("/ospiti/nuovo/<int:id_camera>", methods=["POST"])
def nuovo_ospite(id_camera):
    camera = database.get_camera(id_camera)
    if not camera:
        abort(404)

    nome = request.form.get("nome", "").strip()
    cognome = request.form.get("cognome", "").strip()
    email = request.form.get("email", "").strip()
    telefono = request.form.get("telefono", "").strip()
    nazionalita = request.form.get("nazionalita", "").strip()

    # Validazione campi obbligatori
    if not nome or not cognome or not email:
        flash("Nome, cognome ed email sono obbligatori!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # Controllo lunghezza nome e cognome
    if len(nome) < 2 or len(nome) > 50:
        flash("Il nome deve contenere tra 2 e 50 caratteri!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    if len(cognome) < 2 or len(cognome) > 50:
        flash("Il cognome deve contenere tra 2 e 50 caratteri!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # Controllo formato e lunghezza email
    regex_email = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    if len(email) > 100 or not re.match(regex_email, email):
        flash("Inserisci un indirizzo email valido (es. nome@dominio.it, max 100 caratteri)!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # Controllo formato e caratteri numero di telefono (se inserito)
    if telefono:
        if len(telefono) < 8 or len(telefono) > 20:
            flash("Il numero di telefono deve contenere tra 8 e 20 caratteri!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        # Consente solo cifre, prefisso +, spazi e trattini
        if not re.match(r"^\+?[0-9\s\-]+$", telefono):
            flash("Il numero di telefono può contenere solo cifre, spazi, trattini e il prefisso '+'!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

    # Controllo lunghezza nazionalità (se inserita)
    if nazionalita and len(nazionalita) > 40:
        flash("La nazionalità non può superare i 40 caratteri!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # Controllo duplicato email
    if database.get_ospite_per_email(email):
        flash(f"L'indirizzo email '{email}' appartiene già a un cliente registrato!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # Controllo duplicato telefono (se specificato)
    if telefono and database.get_ospite_per_telefono(telefono):
        flash(f"Il numero di telefono '{telefono}' appartiene già a un cliente registrato!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    id_ospite = database.crea_ospite(nome, cognome, email, telefono, nazionalita)
    flash(f"Nuovo cliente '{cognome} {nome}' registrato con successo!", "success")
    return redirect(url_for("prenota", id_camera=id_camera, id_ospite_selezionato=id_ospite))


# ==============================================================================
# PAGINA 4: LISTA SOGGIORNI (soggiorni.html)
# ==============================================================================
@app.route("/soggiorni")
def soggiorni():
    mostra_tutti = request.args.get("tutti") == "1"

    if mostra_tutti:
        data_da = ""
        data_a = ""
        stato_filtro = ""
        lista_s = database.filtra_soggiorni()
    else:
        # Di default mostriamo tutti i soggiorni dalla data odierna in poi
        data_da = request.args.get("data_da")
        if data_da is None:
            data_da = date.today().isoformat()

        data_a = request.args.get("data_a", "").strip()
        stato_filtro = request.args.get("stato", "").strip()

        lista_s = database.filtra_soggiorni(
            data_da=data_da if data_da else None,
            data_a=data_a if data_a else None,
            stato=stato_filtro if stato_filtro else None
        )

    return render_template("soggiorni.html",
                           soggiorni=lista_s,
                           data_oggi=date.today(),
                           data_da=data_da,
                           data_a=data_a,
                           stato_filtro=stato_filtro,
                           stati_soggiorno=STATI_SOGGIORNO)


@app.route("/soggiorni/stato/<int:id_soggiorno>/<stato>")
def soggiorno_cambia_stato(id_soggiorno, stato):
    if stato not in STATI_SOGGIORNO:
        flash("Stato soggiorno non valido!", "danger")
        return redirect(url_for("soggiorni"))

    soggiorno = database.get_soggiorno(id_soggiorno)
    if not soggiorno:
        abort(404)

    # Impedisce il check-in su soggiorni passati o futuri
    if stato == 'check_in':
        if soggiorno['stato'] != 'prenotato':
            flash(f"Il check-in può essere effettuato solo su prenotazioni attive (stato attuale: '{soggiorno['stato']}')!", "warning")
            return redirect(url_for("soggiorni"))

        if soggiorno['data_checkin'] > date.today():
            flash(f"Impossibile eseguire il check-in: la data di arrivo è futura ({soggiorno['data_checkin'].strftime('%d/%m/%Y')})! Il check-in è consentito solo il giorno di arrivo.", "danger")
            return redirect(url_for("soggiorni"))

        if soggiorno['data_checkin'] < date.today():
            flash(f"Impossibile eseguire il check-in: il soggiorno è passato ({soggiorno['data_checkin'].strftime('%d/%m/%Y')})!", "danger")
            return redirect(url_for("soggiorni"))

        # Impedisce di fare check-in se un altro soggiorno è già in check-in per questa camera
        soggiorno_attivo = database.get_soggiorno_oggi_camera(soggiorno['id_camera'])
        if soggiorno_attivo and soggiorno_attivo['id_soggiorno'] != id_soggiorno and soggiorno_attivo['stato'] == 'check_in':
            flash(f"Impossibile eseguire il check-in: la camera {soggiorno['numero_camera']} è già occupata da un altro soggiorno attivo!", "danger")
            return redirect(url_for("soggiorni"))

    # Il check-out è consentito solo su un soggiorno con ospite attualmente in struttura
    if stato == 'check_out':
        if soggiorno['stato'] != 'check_in':
            flash(f"Il check-out può essere effettuato solo su un soggiorno con ospite in struttura (stato attuale: '{soggiorno['stato']}')!", "warning")
            return redirect(url_for("soggiorni"))

    # L'annullamento è consentito solo su una prenotazione non ancora iniziata
    if stato == 'annullato':
        if soggiorno['stato'] != 'prenotato':
            flash(f"È possibile annullare solo una prenotazione non ancora iniziata (stato attuale: '{soggiorno['stato']}')!", "warning")
            return redirect(url_for("soggiorni"))

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