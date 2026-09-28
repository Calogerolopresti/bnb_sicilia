from csv import excel

import mysql.connector
from mysql.connector.aio import cursor

DB_CONFIG = {
    'host':'localhost',
    'user':'root',
    'password':'Stellina',
    'database':'bnb_sicilia'
}

def get_connection():
    '''Apre e restituisce una connessione al database MySQL.'''
    return mysql.connector.connect(**DB_CONFIG)


def lista(sql,params=()):
    conn=get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql,params)
    risultato = cursor.fetchall()
    cursor.close()
    conn.close()
    return risultato

def riga(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    risultato = cursor.fetchone()
    cursor.close()
    conn.close()
    return risultato

def modifica(sql,params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql,params)
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return last_id


if __name__ == "__main__":
    print("---test---")
    try:
        camere = lista("SELECT * FROM camere ORDER BY numero")
        print(f"connessione riuscita! trovate {len(camere)} nel db")
        for c in camere:
            print(f" - [{c['numero']}] {c['nome']} ({c['tipo']}) - Stato: {c['stato']}")
    except Exception as e:
        print(f"errore durare la connesione al db {e}")
