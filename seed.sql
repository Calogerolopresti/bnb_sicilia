USE bnb_sicilia;

-- Dati di prova per Camere
INSERT INTO camere (numero, nome, tipo, posti, prezzo_notte, stato) VALUES
('101', 'Camera Etna', 'Doppia', 2, 85.00, 'occupata'),
('102', 'Camera Ortigia', 'Matrimoniale', 2, 95.00, 'libera'),
('103', 'Suite Taormina', 'Suite', 4, 150.00, 'libera'),
('104', 'Camera Zagara', 'Singola', 1, 60.00, 'pulizia'),
('105', 'Camera Mandorlo', 'Tripla', 3, 110.00, 'libera');

-- Dati di prova per Ospiti
INSERT INTO ospiti (nome, cognome, email, telefono, nazionalita) VALUES
('Giuseppe', 'Verdi', 'giuseppe.verdi@email.it', '+393331234567', 'Italiana'),
('John', 'Smith', 'john.smith@email.com', '+447700900077', 'Inglese'),
('Marie', 'Curie', 'marie.curie@email.fr', '+33612345678', 'Francese'),
('Marco', 'Rossi', 'marco.rossi@email.it', '+393409876543', 'Italiana'),
('Hans', 'Müller', 'hans.muller@email.de', '+4915123456789', 'Tedesca');

-- Dati di prova per Soggiorni
INSERT INTO soggiorni (id_camera, id_ospite, data_checkin, data_checkout, stato) VALUES
(1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 3 DAY), 'check_in'),
(2, 2, DATE_ADD(CURDATE(), INTERVAL 1 DAY), DATE_ADD(CURDATE(), INTERVAL 5 DAY), 'prenotato'),
(3, 3, DATE_SUB(CURDATE(), INTERVAL 5 DAY), CURDATE(), 'check_out');

-- Dati di prova per Servizi Extra
INSERT INTO servizi_extra (id_soggiorno, nome_servizio, prezzo, data_servizio) VALUES
(1, 'Tour dell\'Etna', 65.00, CURDATE()),
(1, 'Colazione siciliana in terrazza', 12.00, CURDATE()),
(2, 'Transfer aeroporto Catania', 45.00, DATE_ADD(CURDATE(), INTERVAL 1 DAY));