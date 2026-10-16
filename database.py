from datetime import date
import mysql.connector

# parametri di connessione al database mysql locale
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Stellina',
    'database': 'bnb_sicilia'
}


def get_connection():
    # apre e ci passa la connessione pulita al database mysql
    return mysql.connector.connect(**DB_CONFIG)


# ==============================================================================
# i 3 modelli di query standard
# ==============================================================================

def lista(sql, params=()):
    # serve per lanciare le select che restituiscono piu righe sotto forma di lista di dizionari
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def riga(sql, params=()):
    # fa una select puntuale e ci restituisce solo una riga come dizionario oppure none se non c'e nulla
    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def modifica(sql, params=()):
    # serve per insert update e delete con commit immediato e restituisce l'id inserito se c'e
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# sezione 1: camere, ospiti e dashboard
# ==============================================================================

def lista_camere():
    # recupera tutte le camere del bnb ordinate per numero crescente
    return lista("SELECT * FROM camere ORDER BY numero")


def get_camera(id_camera):
    # becca i dettagli di una singola camera usando il suo id
    return riga("SELECT * FROM camere WHERE id_camera = %s", (id_camera,))


def aggiorna_stato_camera(id_camera, stato):
    # cambia lo stato della stanza nel db ad esempio in libera occupata o in pulizia
    return modifica("UPDATE camere SET stato = %s WHERE id_camera = %s", (stato, id_camera))


def lista_ospiti():
    # tira fuori tutti i clienti registrati ordinati in ordine alfabetico per cognome e nome
    return lista("SELECT * FROM ospiti ORDER BY cognome, nome")


def get_ospite(id_ospite):
    # trova la scheda completa di un ospite partendo dal suo id
    return riga("SELECT * FROM ospiti WHERE id_ospite = %s", (id_ospite,))


def crea_ospite(nome, cognome, email, telefono, nazionalita):
    # registra un nuovo cliente nel database e ci ritorna subito il nuovo id generato
    sql = """
        INSERT INTO ospiti (nome, cognome, email, telefono, nazionalita)
        VALUES (%s, %s, %s, %s, %s)
    """
    return modifica(sql, (nome, cognome, email, telefono, nazionalita))


def get_ospite_per_email(email):
    # cerca se c'e gia un ospite con questa email per evitare doppioni
    return riga("SELECT * FROM ospiti WHERE email = %s", (email,))


def get_ospite_per_telefono(telefono):
    # controlla se esiste gia un cliente con questo numero di telefono salvato
    return riga("SELECT * FROM ospiti WHERE telefono = %s", (telefono,))


def conta_camere_per_stato():
    # conta quante camere sono libere quante occupate e quante in pulizia per i badge della dashboard
    return lista("SELECT stato, COUNT(*) AS totale FROM camere GROUP BY stato")


def lista_arrivi_oggi():
    # prende tutti i check-in programmati per la giornata di oggi che risultano ancora come prenotati
    sql = """
        SELECT s.*, c.nome AS nome_camera, c.numero AS numero_camera, o.nome AS nome_ospite, o.cognome AS cognome_ospite
        FROM soggiorni s
        INNER JOIN camere c ON s.id_camera = c.id_camera
        INNER JOIN ospiti o ON s.id_ospite = o.id_ospite
        WHERE s.data_checkin = CURDATE() AND s.stato = 'prenotato'
        ORDER BY c.numero
    """
    return lista(sql)


def lista_partenze_oggi():
    # prende tutti gli ospiti che devono fare il check-out oggi e che hanno ancora lo stato check_in attivo
    sql = """
        SELECT s.*, c.nome AS nome_camera, c.numero AS numero_camera, o.nome AS nome_ospite, o.cognome AS cognome_ospite
        FROM soggiorni s
        INNER JOIN camere c ON s.id_camera = c.id_camera
        INNER JOIN ospiti o ON s.id_ospite = o.id_ospite
        WHERE s.data_checkout = CURDATE() AND s.stato = 'check_in'
        ORDER BY c.numero
    """
    return lista(sql)


# ==============================================================================
# sezione 2: soggiorni ed extra
# ==============================================================================

def filtra_soggiorni(data_da=None, data_a=None, stato=None):
    # fa la ricerca dei soggiorni filtrando per data inizio data fine e stato con query dinamica
    sql = """
        SELECT s.*, c.nome AS nome_camera, c.numero AS numero_camera, o.nome AS nome_ospite, o.cognome AS cognome_ospite
        FROM soggiorni s
        INNER JOIN camere c ON s.id_camera = c.id_camera
        INNER JOIN ospiti o ON s.id_ospite = o.id_ospite
        WHERE 1=1
    """
    params = []

    if data_da:
        sql += " AND s.data_checkout >= %s"
        params.append(data_da)

    if data_a:
        sql += " AND s.data_checkin <= %s"
        params.append(data_a)

    if stato and stato in ['prenotato', 'check_in', 'check_out', 'annullato']:
        sql += " AND s.stato = %s"
        params.append(stato)

    sql += " ORDER BY s.data_checkin ASC"
    return lista(sql, tuple(params))


def get_soggiorno(id_soggiorno):
    # pesca tutti i dettagli di una singola prenotazione compresi dati dell'ospite e info della camera
    sql = """
        SELECT s.*, c.nome AS nome_camera, c.numero AS numero_camera, c.prezzo_notte, 
               o.nome AS nome_ospite, o.cognome AS cognome_ospite, o.email, o.telefono
        FROM soggiorni s
        INNER JOIN camere c ON s.id_camera = c.id_camera
        INNER JOIN ospiti o ON s.id_ospite = o.id_ospite
        WHERE s.id_soggiorno = %s
    """
    return riga(sql, (id_soggiorno,))


def camera_disponibile(id_camera, checkin, checkout):
    # controlla se una stanza e libera in quelle date senza sovrapporsi ad altri soggiorni attivi
    # se le date sono sballate o nel passato blocca subito
    if checkout <= checkin or checkin < date.today():
        return False

    sql = """
        SELECT COUNT(*) AS n 
        FROM soggiorni 
        WHERE id_camera = %s 
          AND stato IN ('prenotato', 'check_in') 
          AND data_checkin < %s 
          AND data_checkout > %s
    """
    ris = riga(sql, (id_camera, checkout, checkin))
    return (ris['n'] == 0) if ris else True


def lista_prenotazioni_camera(id_camera):
    # prende tutte le prenotazioni attive o future di una stanza specifica per mostrarle nel box laterale
    sql = """
        SELECT s.*, o.nome AS nome_ospite, o.cognome AS cognome_ospite
        FROM soggiorni s
        INNER JOIN ospiti o ON s.id_ospite = o.id_ospite
        WHERE s.id_camera = %s 
          AND s.stato IN ('prenotato', 'check_in')
          AND s.data_checkout >= CURDATE()
        ORDER BY s.data_checkin ASC
    """
    return lista(sql, (id_camera,))


def crea_soggiorno(id_camera, id_ospite, checkin, checkout):
    # inserisce una nuova prenotazione collegando camera e cliente con stato iniziale prenotato
    sql = """
        INSERT INTO soggiorni (id_camera, id_ospite, data_checkin, data_checkout, stato)
        VALUES (%s, %s, %s, %s, 'prenotato')
    """
    return modifica(sql, (id_camera, id_ospite, checkin, checkout))


def aggiorna_stato_soggiorno(id_soggiorno, stato):
    # cambia lo stato della prenotazione ad esempio quando il cliente arriva fa check-in o check-out
    return modifica("UPDATE soggiorni SET stato = %s WHERE id_soggiorno = %s", (stato, id_soggiorno))


def get_soggiorno_attivo_camera(id_camera):
    # controlla se in quella camera c'e gia qualcuno dentro con check-in fatto
    sql = """
        SELECT * FROM soggiorni
        WHERE id_camera = %s AND stato = 'check_in'
        LIMIT 1
    """
    return riga(sql, (id_camera,))


def get_soggiorno_arrivo_oggi_camera(id_camera):
    # vede se per quella stanza c'e una prenotazione con arrivo previsto esattamente oggi
    sql = """
        SELECT * FROM soggiorni
        WHERE id_camera = %s AND stato = 'prenotato' AND data_checkin = CURDATE()
        LIMIT 1
    """
    return riga(sql, (id_camera,))


def lista_id_camere_con_ospite_presente():
    # restituisce una lista con gli id delle stanze che hanno un ospite fisicamente dentro
    righe = lista("SELECT DISTINCT id_camera FROM soggiorni WHERE stato = 'check_in'")
    return [r['id_camera'] for r in righe]


def annulla_soggiorni_camera(id_camera):
    # annulla il soggiorno di oggi se la camera viene liberata a mano dal gestore cosi non blocca il db
    sql = """
        UPDATE soggiorni SET stato = 'annullato'
        WHERE id_camera = %s AND stato IN ('prenotato', 'check_in')
          AND data_checkin <= CURDATE() AND data_checkout >= CURDATE()
    """
    return modifica(sql, (id_camera,))


def lista_extra_soggiorno(id_soggiorno):
    # tira fuori tutti i servizi extra addebitati a questo soggiorno
    sql = "SELECT * FROM servizi_extra WHERE id_soggiorno = %s ORDER BY data_servizio"
    return lista(sql, (id_soggiorno,))


def totale_extra(id_soggiorno):
    # somma i prezzi di tutti gli extra del soggiorno gestendo anche il caso in cui non ce ne siano
    sql = "SELECT COALESCE(SUM(prezzo), 0) AS totale FROM servizi_extra WHERE id_soggiorno = %s"
    ris = riga(sql, (id_soggiorno,))
    return ris['totale'] if ris else 0.00


def aggiungi_extra(id_soggiorno, nome, prezzo, data):
    # salva nel db un nuovo extra consumato dall'ospite come tour colazioni o transfer
    sql = """
        INSERT INTO servizi_extra (id_soggiorno, nome_servizio, prezzo, data_servizio)
        VALUES (%s, %s, %s, %s)
    """
    return modifica(sql, (id_soggiorno, nome, prezzo, data))


def get_extra(id_extra, id_soggiorno):
    # trova un extra specifico verificando che appartenga davvero a quel soggiorno
    sql = "SELECT * FROM servizi_extra WHERE id_extra = %s AND id_soggiorno = %s"
    return riga(sql, (id_extra, id_soggiorno))


def rimuovi_extra(id_extra, id_soggiorno):
    # elimina un servizio extra dal db solo se e associato al soggiorno giusto
    sql = "DELETE FROM servizi_extra WHERE id_extra = %s AND id_soggiorno = %s"
    return modifica(sql, (id_extra, id_soggiorno))


# ==============================================================================
# test delle funzioni
# ==============================================================================
if __name__ == "__main__":
    print("--- test funzioni database ---")
    print("camere nel sistema:", len(lista_camere()))
    print("ospiti nel sistema:", len(lista_ospiti()))
    print("soggiorni nel sistema:", len(filtra_soggiorni()))