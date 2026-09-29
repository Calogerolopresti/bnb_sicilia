CREATE DATABASE IF NOT EXISTS bnb_sicilia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bnb_sicilia;

-- Eliminazione tabelle se esistono già (per reset)
DROP TABLE IF EXISTS servizi_extra;
DROP TABLE IF EXISTS soggiorni;
DROP TABLE IF EXISTS ospiti;
DROP TABLE IF EXISTS camere;

-- 1. Tabella CAMERE
CREATE TABLE camere (
    id_camera     INT AUTO_INCREMENT PRIMARY KEY,
    numero        VARCHAR(10)  NOT NULL UNIQUE,
    nome          VARCHAR(60)  NOT NULL,
    tipo          VARCHAR(30)  NOT NULL,
    posti         TINYINT      NOT NULL,
    prezzo_notte  DECIMAL(8,2) NOT NULL,
    stato         ENUM('libera','occupata','pulizia') NOT NULL DEFAULT 'libera'
);

-- 2. Tabella OSPITI
CREATE TABLE ospiti (
    id_ospite     INT AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(50)  NOT NULL,
    cognome       VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) NOT NULL,
    telefono      VARCHAR(20),
    nazionalita   VARCHAR(40)
);

-- 3. Tabella SOGGIORNI
CREATE TABLE soggiorni (
    id_soggiorno  INT AUTO_INCREMENT PRIMARY KEY,
    id_camera     INT  NOT NULL,
    id_ospite     INT  NOT NULL,
    data_checkin  DATE NOT NULL,
    data_checkout DATE NOT NULL,
    stato         ENUM('prenotato','check_in','check_out','annullato') NOT NULL DEFAULT 'prenotato',
    FOREIGN KEY (id_camera) REFERENCES camere(id_camera),
    FOREIGN KEY (id_ospite) REFERENCES ospiti(id_ospite)
);

-- 4. Tabella SERVIZI_EXTRA
CREATE TABLE servizi_extra (
    id_extra      INT AUTO_INCREMENT PRIMARY KEY,
    id_soggiorno  INT           NOT NULL,
    nome_servizio VARCHAR(80)   NOT NULL,
    prezzo        DECIMAL(8,2)  NOT NULL,
    data_servizio DATE          NOT NULL,
    FOREIGN KEY (id_soggiorno) REFERENCES soggiorni(id_soggiorno)
);