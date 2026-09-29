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
    cursor.execute(sql, params)
    risultato = cursor.fetchall()
    cursor.close()
    conn.close()
    return risultato


def riga(sql, params=()):
    """Modello 2: Esegue query SELECT e restituisce una sola riga o None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    risultato = cursor.fetchone()
    cursor.close()
    conn.close()
    return risultato


def modifica(sql, params=()):
    """Modello 3: Esegue INSERT, UPDATE, DELETE con commit."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return last_id


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

def lista_soggiorni():
    """Restituisce tutti i soggiorni con i dati di camera e ospite (INNER JOIN)."""
    sql = """
        SELECT s.*, c.nome AS nome_camera, c.numero AS numero_camera, o.nome AS nome_ospite, o.cognome AS cognome_ospite
        FROM soggiorni s
        INNER JOIN camere c ON s.id_camera = c.id_camera
        INNER JOIN ospiti o ON s.id_ospite = o.id_ospite
        ORDER BY s.data_checkin DESC
    """
    return lista(sql)


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
    sql = """
        SELECT COUNT(*) AS n 
        FROM soggiorni 
        WHERE id_camera = %s 
          AND stato IN ('prenotato', 'check_in') 
          AND data_checkin < %s 
          AND data_checkout > %s
    """
    ris = riga(sql, (id_camera, checkout, checkin))
    return ris['n'] == 0


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


def rimuovi_extra(id_extra):
    """Elimina un servizio extra."""
    return modifica("DELETE FROM servizi_extra WHERE id_extra = %s", (id_extra,))


# ==============================================================================
# TEST DELLE FUNZIONI
# ==============================================================================
if __name__ == "__main__":
    print("--- TEST FUNZIONI DATABASE ---")
    print("Camere nel sistema:", len(lista_camere()))
    print("Ospiti nel sistema:", len(lista_ospiti()))
    print("Soggiorni nel sistema:", len(lista_soggiorni()))