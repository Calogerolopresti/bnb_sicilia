from datetime import date
import mysql.connector

# CONFIGURAZIONE CONNESSIONE MYSQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Stellina',
    'database': 'bnb_sicilia'
}


def get_connection():
    """Apre e restituisce una connessione al database MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


# ==============================================================================
# I 3 MODELLI DI QUERY STANDARD
# ==============================================================================

def lista(sql, params=()):
    """Modello 1: Esegue query SELECT e restituisce una lista di dizionari."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def riga(sql, params=()):
    """Modello 2: Esegue query SELECT e restituisce una sola riga o None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def modifica(sql, params=()):
    """Modello 3: Esegue INSERT, UPDATE, DELETE con commit."""
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
# SEZIONE 1: CAMERE, OSPITI E DASHBOARD
# ==============================================================================

def lista_camere():
    """Restituisce la lista di tutte le camere ordinate per numero."""
    return lista("SELECT * FROM camere ORDER BY numero")


def get_camera(id_camera):
    """Restituisce i dettagli di una singola camera tramite ID."""
    return riga("SELECT * FROM camere WHERE id_camera = %s", (id_camera,))


def aggiorna_stato_camera(id_camera, stato):
    """Aggiorna lo stato di una camera (libera, occupata, pulizia)."""
    return modifica("UPDATE camere SET stato = %s WHERE id_camera = %s", (stato, id_camera))


def lista_ospiti():
    """Restituisce la lista degli ospiti ordinati per cognome."""
    return lista("SELECT * FROM ospiti ORDER BY cognome, nome")


def get_ospite(id_ospite):
    """Restituisce i dettagli di un singolo ospite tramite ID."""
    return riga("SELECT * FROM ospiti WHERE id_ospite = %s", (id_ospite,))


def crea_ospite(nome, cognome, email, telefono, nazionalita):
    """Inserisce un nuovo ospite nel database e restituisce il suo ID."""
    sql = """
        INSERT INTO ospiti (nome, cognome, email, telefono, nazionalita)
        VALUES (%s, %s, %s, %s, %s)
    """
    return modifica(sql, (nome, cognome, email, telefono, nazionalita))


def get_ospite_per_email(email):
    """Restituisce l'ospite associato a un dato indirizzo email se presente."""
    return riga("SELECT * FROM ospiti WHERE email = %s", (email,))


def get_ospite_per_telefono(telefono):
    """Restituisce l'ospite associato a un dato numero di telefono se presente."""
    return riga("SELECT * FROM ospiti WHERE telefono = %s", (telefono,))


def conta_camere_per_stato():
    """Conta quante camere ci sono per ciascuno stato."""
    return lista("SELECT stato, COUNT(*) AS totale FROM camere GROUP BY stato")


def lista_arrivi_oggi():
    """Mostra i soggiorni con check-in previsto per oggi e stato 'prenotato'."""
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
    """Mostra i soggiorni con check-out previsto per oggi e stato 'check_in'."""
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
# SEZIONE 2: SOGGIORNI ED EXTRA
# ==============================================================================

def filtra_soggiorni(data_da=None, data_a=None, stato=None):
    """Restituisce i soggiorni filtrati per intervallo date e/o stato."""
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
    """Restituisce il dettaglio di un soggiorno includendo i dati della camera e dell'ospite."""
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
    """Controlla se una camera è già prenotata o occupata nelle date selezionate."""
    # Non è disponibile per date passate o non valide
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
    """Restituisce le prenotazioni attive o future per una camera per visualizzarle nel riepilogo."""
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
    """Registra un nuovo soggiorno e restituisce l'ID creato."""
    sql = """
        INSERT INTO soggiorni (id_camera, id_ospite, data_checkin, data_checkout, stato)
        VALUES (%s, %s, %s, %s, 'prenotato')
    """
    return modifica(sql, (id_camera, id_ospite, checkin, checkout))


def aggiorna_stato_soggiorno(id_soggiorno, stato):
    """Aggiorna lo stato di un soggiorno."""
    return modifica("UPDATE soggiorni SET stato = %s WHERE id_soggiorno = %s", (stato, id_soggiorno))


def get_soggiorno_attivo_camera(id_camera):
    """Restituisce il soggiorno con ospite attualmente in check-in nella camera, se presente."""
    sql = """
        SELECT * FROM soggiorni
        WHERE id_camera = %s AND stato = 'check_in'
        LIMIT 1
    """
    return riga(sql, (id_camera,))


def get_soggiorno_arrivo_oggi_camera(id_camera):
    """Restituisce la prenotazione con arrivo previsto oggi nella camera, se presente."""
    sql = """
        SELECT * FROM soggiorni
        WHERE id_camera = %s AND stato = 'prenotato' AND data_checkin = CURDATE()
        LIMIT 1
    """
    return riga(sql, (id_camera,))


def lista_id_camere_con_ospite_presente():
    """Restituisce gli ID delle camere con un ospite attualmente in check-in."""
    righe = lista("SELECT DISTINCT id_camera FROM soggiorni WHERE stato = 'check_in'")
    return [r['id_camera'] for r in righe]


def annulla_soggiorni_camera(id_camera):
    """Annulla solo il soggiorno di oggi (non le prenotazioni future) quando la camera viene liberata manualmente."""
    sql = """
        UPDATE soggiorni SET stato = 'annullato'
        WHERE id_camera = %s AND stato IN ('prenotato', 'check_in')
          AND data_checkin <= CURDATE() AND data_checkout >= CURDATE()
    """
    return modifica(sql, (id_camera,))


def lista_extra_soggiorno(id_soggiorno):
    """Restituisce i servizi extra aggiunti ad un specifico soggiorno."""
    sql = "SELECT * FROM servizi_extra WHERE id_soggiorno = %s ORDER BY data_servizio"
    return lista(sql, (id_soggiorno,))


def totale_extra(id_soggiorno):
    """Calcola il costo totale degli extra per un soggiorno (usa COALESCE per evitare NULL)."""
    sql = "SELECT COALESCE(SUM(prezzo), 0) AS totale FROM servizi_extra WHERE id_soggiorno = %s"
    ris = riga(sql, (id_soggiorno,))
    return ris['totale'] if ris else 0.00


def aggiungi_extra(id_soggiorno, nome, prezzo, data):
    """Aggiunge un servizio extra al soggiorno."""
    sql = """
        INSERT INTO servizi_extra (id_soggiorno, nome_servizio, prezzo, data_servizio)
        VALUES (%s, %s, %s, %s)
    """
    return modifica(sql, (id_soggiorno, nome, prezzo, data))


def get_extra(id_extra, id_soggiorno):
    """Restituisce un servizio extra solo se appartiene al soggiorno indicato."""
    sql = "SELECT * FROM servizi_extra WHERE id_extra = %s AND id_soggiorno = %s"
    return riga(sql, (id_extra, id_soggiorno))


def rimuovi_extra(id_extra, id_soggiorno):
    """Elimina un servizio extra, solo se appartiene al soggiorno indicato."""
    sql = "DELETE FROM servizi_extra WHERE id_extra = %s AND id_soggiorno = %s"
    return modifica(sql, (id_extra, id_soggiorno))


# ==============================================================================
# TEST DELLE FUNZIONI
# ==============================================================================
if __name__ == "__main__":
    print("--- TEST FUNZIONI DATABASE ---")
    print("Camere nel sistema:", len(lista_camere()))
    print("Ospiti nel sistema:", len(lista_ospiti()))
    print("Soggiorni nel sistema:", len(filtra_soggiorni()))