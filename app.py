import re
from datetime import date, timedelta
import mysql.connector
from flask import Flask, render_template, redirect, url_for, flash, abort, request
import database

app = Flask(__name__)
app.secret_key = "bnb_sicilia_secret_key_super_sicura"

# ==============================================================================
# costanti e whitelist
# ==============================================================================
STATI_CAMERA = ['libera', 'occupata', 'pulizia']
STATI_SOGGIORNO = ['prenotato', 'check_in', 'check_out', 'annullato']

# listino dei servizi extra che l'ospite puo richiedere durante il soggiorno
CATALOGO_EXTRA = {
    1: ("Tour dell'Etna", 65.00),
    2: ("Degustazione vini etnei", 35.00),
    3: ("Transfer aeroporto Catania", 45.00),
    4: ("Colazione siciliana in terrazza", 12.00),
    5: ("Cooking class arancine e cannoli", 50.00),
}


# ==============================================================================
# pagina 1: dashboard (index.html)
# ==============================================================================
@app.route("/")
def index():
    # pagina principale con il quadro generale: camere libere/occupate e arrivi/partenze di oggi
    camere_stato = database.conta_camere_per_stato()
    arrivi = database.lista_arrivi_oggi()
    partenze = database.lista_partenze_oggi()

    # prepariamo il dizionario dei contatori da passare alla vista
    totali = {'libera': 0, 'occupata': 0, 'pulizia': 0}
    for item in camere_stato:
        totali[item['stato']] = item['totale']

    return render_template("index.html", totali=totali, arrivi=arrivi, partenze=partenze)


# ==============================================================================
# pagina 2: gestione camere (camere.html)
# ==============================================================================
@app.route("/camere")
def camere():
    # mostra la griglia di tutte le stanze con il loro stato e indica quali hanno ospiti dentro
    lista_c = database.lista_camere()
    camere_con_ospite = database.lista_id_camere_con_ospite_presente()
    return render_template("camere.html", camere=lista_c, camere_con_ospite=camere_con_ospite)


@app.route("/camere/stato/<int:id_camera>/<stato>")
def camere_cambia_stato(id_camera, stato):
    # cambia al volo lo stato di una stanza (es. da pulizia a libera o occupata) con i dovuti controlli
    if stato not in STATI_CAMERA:
        flash("Stato camera non valido!", "danger")
        return redirect(url_for("camere"))

    camera = database.get_camera(id_camera)
    if not camera:
        abort(404)

    # se vogliamo metterla 'occupata', deve esserci un ospite gia presente o che arriva oggi
    if stato == 'occupata':
        if not database.get_soggiorno_attivo_camera(id_camera):
            soggiorno_arrivo = database.get_soggiorno_arrivo_oggi_camera(id_camera)
            if not soggiorno_arrivo:
                flash(f"Impossibile impostare la camera {camera['numero']} come occupata: non risulta alcun ospite presente o in arrivo oggi!", "warning")
                return redirect(url_for("camere"))
            database.aggiorna_stato_soggiorno(soggiorno_arrivo['id_soggiorno'], 'check_in')

    # non possiamo metterla in pulizia se l'ospite e ancora dentro la stanza
    if stato == 'pulizia':
        if database.get_soggiorno_attivo_camera(id_camera):
            flash(f"Impossibile impostare la camera {camera['numero']} in pulizia: c'è ancora un ospite in check-in!", "warning")
            return redirect(url_for("camere"))

    # aggiorna lo stato nel database
    database.aggiorna_stato_camera(id_camera, stato)

    # se liberiamo la stanza a mano, annulliamo il soggiorno di oggi per non lasciare date bloccate
    if stato == 'libera':
        database.annulla_soggiorni_camera(id_camera)

    flash(f"Stato della camera {camera['numero']} aggiornato in '{stato}'.", "success")
    return redirect(url_for("camere"))


# ==============================================================================
# pagina 3: nuova prenotazione (prenota.html)
# ==============================================================================
@app.route("/prenota/<int:id_camera>", methods=["GET", "POST"])
def prenota(id_camera):
    # gestisce la prenotazione di una stanza specifica: convalida date, controlla conflitti e salva
    camera = database.get_camera(id_camera)
    if not camera:
        abort(404)

    if request.method == "POST":
        id_ospite = request.form.get("id_ospite")
        checkin_str = request.form.get("checkin")
        checkout_str = request.form.get("checkout")

        # controlla che tutti i campi necessari siano compilati
        if not id_ospite or not checkin_str or not checkout_str:
            flash("Compila tutti i campi obbligatori per completare la prenotazione!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        try:
            checkin = date.fromisoformat(checkin_str)
            checkout = date.fromisoformat(checkout_str)
        except ValueError:
            flash("Formato data non valido!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        # blocca date passate o checkout antecedente al checkin
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

        # verifica che la stanza non sia gia prenotata da qualcun altro in quel range di date
        if not database.camera_disponibile(id_camera, checkin, checkout):
            flash(f"La camera {camera['numero']} non è disponibile per le date selezionate ({checkin.strftime('%d/%m/%Y')} - {checkout.strftime('%d/%m/%Y')}): c'è già una prenotazione per quel periodo!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        # se la prenotazione inizia oggi e la camera e gia occupata non possiamo piazzarlo
        if checkin <= date.today() < checkout and camera['stato'] == 'occupata':
            flash(f"Impossibile completare la prenotazione: la camera {camera['numero']} risulta attualmente già occupata!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        try:
            id_soggiorno = database.crea_soggiorno(id_camera, id_ospite, checkin, checkout)
        except mysql.connector.IntegrityError:
            flash("Impossibile completare la prenotazione: le date non sono valide o sono in conflitto.", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        # se parte da oggi mettiamo subito la stanza su 'occupata'
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
    # registra al volo un nuovo ospite dal modale della prenotazione con tutte le validazioni
    camera = database.get_camera(id_camera)
    if not camera:
        abort(404)

    nome = request.form.get("nome", "").strip()
    cognome = request.form.get("cognome", "").strip()
    email = request.form.get("email", "").strip()
    telefono = request.form.get("telefono", "").strip()
    nazionalita = request.form.get("nazionalita", "").strip()

    # controlla che i dati obbligatori siano inseriti
    if not nome or not cognome or not email:
        flash("Nome, cognome ed email sono obbligatori!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # controlla la lunghezza valida di nome e cognome
    if len(nome) < 2 or len(nome) > 50:
        flash("Il nome deve contenere tra 2 e 50 caratteri!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    if len(cognome) < 2 or len(cognome) > 50:
        flash("Il cognome deve contenere tra 2 e 50 caratteri!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # verifica che l'email abbia un formato sensato
    regex_email = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    if len(email) > 100 or not re.match(regex_email, email):
        flash("Inserisci un indirizzo email valido (es. nome@dominio.it, max 100 caratteri)!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # se ha inserito il telefono controlla lunghezza e caratteri ammessi
    if telefono:
        if len(telefono) < 8 or len(telefono) > 20:
            flash("Il numero di telefono deve contenere tra 8 e 20 caratteri!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

        # accetta solo numeri, spazi, trattini o prefisso con piu
        if not re.match(r"^\+?[0-9\s\-]+$", telefono):
            flash("Il numero di telefono può contenere solo cifre, spazi, trattini e il prefisso '+'!", "danger")
            return redirect(url_for("prenota", id_camera=id_camera))

    # controlla che la nazionalita non sia troppo lunga
    if nazionalita and len(nazionalita) > 40:
        flash("La nazionalità non può superare i 40 caratteri!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # controlla se l'email e gia registrata per non creare doppioni
    if database.get_ospite_per_email(email):
        flash(f"L'indirizzo email '{email}' appartiene già a un cliente registrato!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    # controlla se il telefono e gia associato ad un altro ospite
    if telefono and database.get_ospite_per_telefono(telefono):
        flash(f"Il numero di telefono '{telefono}' appartiene già a un cliente registrato!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    try:
        id_ospite = database.crea_ospite(nome, cognome, email, telefono, nazionalita)
    except mysql.connector.IntegrityError:
        flash(f"L'indirizzo email '{email}' appartiene già a un cliente registrato!", "danger")
        return redirect(url_for("prenota", id_camera=id_camera))

    flash(f"Nuovo cliente '{cognome} {nome}' registrato con successo!", "success")
    return redirect(url_for("prenota", id_camera=id_camera, id_ospite_selezionato=id_ospite))


# ==============================================================================
# pagina 4: lista soggiorni (soggiorni.html)
# ==============================================================================
@app.route("/soggiorni")
def soggiorni():
    # mostra l'elenco dei soggiorni con possibilita di filtrare per data o stato
    mostra_tutti = request.args.get("tutti") == "1"

    if mostra_tutti:
        data_da = ""
        data_a = ""
        stato_filtro = ""
        filtro_da_oggi = False
        lista_s = database.filtra_soggiorni()
    else:
        # di default partiamo mostrando i soggiorni da oggi in avanti
        data_da = request.args.get("data_da")
        filtro_da_oggi = data_da is None
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
                           filtro_da_oggi=filtro_da_oggi,
                           stati_soggiorno=STATI_SOGGIORNO)


@app.route("/soggiorni/stato/<int:id_soggiorno>/<stato>")
def soggiorno_cambia_stato(id_soggiorno, stato):
    # gestisce i passaggi di stato: check-in, check-out o annullamento e sincronizza la camera
    if stato not in STATI_SOGGIORNO:
        flash("Stato soggiorno non valido!", "danger")
        return redirect(url_for("soggiorni"))

    soggiorno = database.get_soggiorno(id_soggiorno)
    if not soggiorno:
        abort(404)

    # il check-in si puo fare solo oggi e se la prenotazione e attiva
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

        # controlla che la stanza non sia gia occupata da un altro ospite in check-in
        soggiorno_attivo = database.get_soggiorno_attivo_camera(soggiorno['id_camera'])
        if soggiorno_attivo and soggiorno_attivo['id_soggiorno'] != id_soggiorno:
            flash(f"Impossibile eseguire il check-in: la camera {soggiorno['numero_camera']} è già occupata da un altro soggiorno attivo!", "danger")
            return redirect(url_for("soggiorni"))

    # il check-out si puo fare solo se l'ospite e gia fisicamente dentro la camera
    if stato == 'check_out':
        if soggiorno['stato'] != 'check_in':
            flash(f"Il check-out può essere effettuato solo su un soggiorno con ospite in struttura (stato attuale: '{soggiorno['stato']}')!", "warning")
            return redirect(url_for("soggiorni"))

    # possiamo annullare solo prenotazioni future o non ancora iniziate
    if stato == 'annullato':
        if soggiorno['stato'] != 'prenotato':
            flash(f"È possibile annullare solo una prenotazione non ancora iniziata (stato attuale: '{soggiorno['stato']}')!", "warning")
            return redirect(url_for("soggiorni"))

    database.aggiorna_stato_soggiorno(id_soggiorno, stato)

    # aggiorna in automatico anche la stanza: se fai check-in va a occupata, check-out a pulizia, annulla a libera
    if stato == 'check_in':
        database.aggiorna_stato_camera(soggiorno['id_camera'], 'occupata')
    elif stato == 'check_out':
        database.aggiorna_stato_camera(soggiorno['id_camera'], 'pulizia')
    elif stato == 'annullato':
        database.aggiorna_stato_camera(soggiorno['id_camera'], 'libera')

    flash(f"Soggiorno aggiornato allo stato '{stato}'.", "success")
    return redirect(url_for("soggiorni"))


# ==============================================================================
# pagina 5: dettaglio soggiorno ed extra (soggiorno.html)
# ==============================================================================
@app.route("/soggiorno/<int:id_soggiorno>")
def soggiorno_dettaglio(id_soggiorno):
    # mostra il conto completo del soggiorno: prezzo delle notti piu tutti i servizi extra
    soggiorno = database.get_soggiorno(id_soggiorno)
    if not soggiorno:
        abort(404)

    extra_lista = database.lista_extra_soggiorno(id_soggiorno)
    tot_extra = database.totale_extra(id_soggiorno)

    # calcola il numero di notti e fa la somma totale tra camera ed extra
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
    # aggiunge al conto del soggiorno uno degli extra presenti nel menu (es. tour dell'etna o colazione)
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
    # cancella un servizio extra dal conto del soggiorno se e stato aggiunto per sbaglio
    extra = database.get_extra(id_extra, id_soggiorno)
    if not extra:
        flash("Servizio extra non trovato per questo soggiorno: impossibile rimuoverlo.", "danger")
        return redirect(url_for("soggiorno_dettaglio", id_soggiorno=id_soggiorno))

    database.rimuovi_extra(id_extra, id_soggiorno)
    flash("Servizio extra rimosso con successo.", "success")
    return redirect(url_for("soggiorno_dettaglio", id_soggiorno=id_soggiorno))


if __name__ == "__main__":
    app.run(debug=True, port=5001)