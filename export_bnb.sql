-- MySQL dump 10.13  Distrib 26.7.0, for macos26.6 (arm64)
--
-- Host: localhost    Database: bnb_sicilia
-- ------------------------------------------------------
-- Server version	26.7.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '4a0e7c28-b82f-11f1-9eda-2a5e59a53105:1-286';

--
-- Table structure for table `camere`
--

DROP TABLE IF EXISTS `camere`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `camere` (
  `id_camera` int NOT NULL AUTO_INCREMENT,
  `numero` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nome` varchar(60) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `posti` tinyint NOT NULL,
  `prezzo_notte` decimal(8,2) NOT NULL,
  `stato` enum('libera','occupata','pulizia') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'libera',
  PRIMARY KEY (`id_camera`),
  UNIQUE KEY `numero` (`numero`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `camere`
--

LOCK TABLES `camere` WRITE;
/*!40000 ALTER TABLE `camere` DISABLE KEYS */;
INSERT INTO `camere` VALUES (1,'101','Camera Etna','Doppia',2,85.00,'occupata'),(2,'102','Camera Ortigia','Matrimoniale',2,95.00,'libera'),(3,'103','Suite Taormina','Suite',4,150.00,'libera'),(4,'104','Camera Zagara','Singola',1,60.00,'pulizia'),(5,'105','Camera Mandorlo','Tripla',3,110.00,'libera');
/*!40000 ALTER TABLE `camere` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ospiti`
--

DROP TABLE IF EXISTS `ospiti`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ospiti` (
  `id_ospite` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cognome` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nazionalita` varchar(40) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id_ospite`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ospiti`
--

LOCK TABLES `ospiti` WRITE;
/*!40000 ALTER TABLE `ospiti` DISABLE KEYS */;
INSERT INTO `ospiti` VALUES (1,'Giuseppe','Verdi','giuseppe.verdi@email.it','+393331234567','Italiana'),(2,'John','Smith','john.smith@email.com','+447700900077','Inglese'),(3,'Marie','Curie','marie.curie@email.fr','+33612345678','Francese'),(4,'Marco','Rossi','marco.rossi@email.it','+393409876543','Italiana'),(5,'Hans','Müller','hans.muller@email.de','+4915123456789','Tedesca'),(6,'francesca','rinallo','rinallofranciiu@gmail.com','3334445555','italiana');
/*!40000 ALTER TABLE `ospiti` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servizi_extra`
--

DROP TABLE IF EXISTS `servizi_extra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servizi_extra` (
  `id_extra` int NOT NULL AUTO_INCREMENT,
  `id_soggiorno` int NOT NULL,
  `nome_servizio` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `prezzo` decimal(8,2) NOT NULL,
  `data_servizio` date NOT NULL,
  PRIMARY KEY (`id_extra`),
  KEY `id_soggiorno` (`id_soggiorno`),
  CONSTRAINT `servizi_extra_ibfk_1` FOREIGN KEY (`id_soggiorno`) REFERENCES `soggiorni` (`id_soggiorno`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servizi_extra`
--

LOCK TABLES `servizi_extra` WRITE;
/*!40000 ALTER TABLE `servizi_extra` DISABLE KEYS */;
INSERT INTO `servizi_extra` VALUES (1,1,'Tour dell\'Etna',65.00,'2026-10-02'),(2,1,'Colazione siciliana in terrazza',12.00,'2026-10-02'),(3,2,'Transfer aeroporto Catania',45.00,'2026-10-03'),(4,4,'Tour dell\'Etna',65.00,'2026-10-02'),(5,4,'Transfer aeroporto Catania',45.00,'2026-10-02'),(6,4,'Degustazione vini etnei',35.00,'2026-10-02'),(7,4,'Colazione siciliana in terrazza',12.00,'2026-10-02'),(8,4,'Cooking class arancine e cannoli',50.00,'2026-10-02');
/*!40000 ALTER TABLE `servizi_extra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `soggiorni`
--

DROP TABLE IF EXISTS `soggiorni`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `soggiorni` (
  `id_soggiorno` int NOT NULL AUTO_INCREMENT,
  `id_camera` int NOT NULL,
  `id_ospite` int NOT NULL,
  `data_checkin` date NOT NULL,
  `data_checkout` date NOT NULL,
  `stato` enum('prenotato','check_in','check_out','annullato') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'prenotato',
  PRIMARY KEY (`id_soggiorno`),
  KEY `id_camera` (`id_camera`),
  KEY `id_ospite` (`id_ospite`),
  CONSTRAINT `soggiorni_ibfk_1` FOREIGN KEY (`id_camera`) REFERENCES `camere` (`id_camera`),
  CONSTRAINT `soggiorni_ibfk_2` FOREIGN KEY (`id_ospite`) REFERENCES `ospiti` (`id_ospite`),
  CONSTRAINT `chk_soggiorni_date` CHECK ((`data_checkout` > `data_checkin`))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `soggiorni`
--

LOCK TABLES `soggiorni` WRITE;
/*!40000 ALTER TABLE `soggiorni` DISABLE KEYS */;
INSERT INTO `soggiorni` VALUES (1,1,1,'2026-10-02','2026-10-05','check_in'),(2,2,2,'2026-10-03','2026-10-07','prenotato'),(3,3,3,'2026-09-27','2026-10-02','check_out'),(4,2,6,'2026-10-07','2026-10-11','annullato');
/*!40000 ALTER TABLE `soggiorni` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-15 17:36:17
