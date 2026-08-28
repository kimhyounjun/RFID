-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: rfid_dabase
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `purchase_history`
--

DROP TABLE IF EXISTS `purchase_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `purchased_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `total_price` int NOT NULL,
  `items` json NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_history`
--

LOCK TABLES `purchase_history` WRITE;
/*!40000 ALTER TABLE `purchase_history` DISABLE KEYS */;
INSERT INTO `purchase_history` VALUES (1,'2025-11-22 19:43:21',6500,'[{\"qty\": 2, \"name\": \"라면\", \"unit_price\": 1500}, {\"qty\": 1, \"name\": \"콜라\", \"unit_price\": 2000}]'),(2,'2025-11-22 19:38:21',3000,'[{\"qty\": 2, \"name\": \"새우깡\", \"unit_price\": 1500}]'),(3,'2025-11-22 19:33:21',7000,'[{\"qty\": 5, \"name\": \"초코우유\", \"unit_price\": 1400}]'),(4,'2025-11-22 11:05:35',2300,'[{\"qty\": 1, \"name\": \"제로콜라\", \"unit_price\": 2300}]'),(5,'2025-11-22 11:09:28',7500,'[{\"qty\": 1, \"name\": \"사이다\", \"unit_price\": 2300}, {\"qty\": 2, \"name\": \"생수\", \"unit_price\": 700}, {\"qty\": 1, \"name\": \"마이쮸\", \"unit_price\": 1000}, {\"qty\": 1, \"name\": \"껌\", \"unit_price\": 500}, {\"qty\": 1, \"name\": \"제로콜라\", \"unit_price\": 2300}]'),(6,'2025-11-24 02:53:13',2300,'[{\"qty\": 1, \"name\": \"사이다\", \"unit_price\": 2300}]'),(7,'2025-11-24 03:07:56',3000,'[{\"qty\": 1, \"name\": \"사이다\", \"unit_price\": 2300}, {\"qty\": 1, \"name\": \"생수\", \"unit_price\": 700}]'),(8,'2025-11-24 18:20:31',1000,'[{\"qty\": 1, \"name\": \"마이쮸\", \"unit_price\": 1000}]'),(9,'2025-11-24 20:13:13',8700,'[{\"qty\": 3, \"name\": \"생수\", \"unit_price\": 700}, {\"qty\": 2, \"name\": \"마이쮸\", \"unit_price\": 1000}, {\"qty\": 2, \"name\": \"사이다\", \"unit_price\": 2300}]'),(10,'2025-11-24 20:29:56',12300,'[{\"qty\": 2, \"name\": \"사이다\", \"unit_price\": 2300}, {\"qty\": 2, \"name\": \"생수\", \"unit_price\": 700}, {\"qty\": 2, \"name\": \"솜사탕\", \"unit_price\": 1500}, {\"qty\": 1, \"name\": \"마이쮸\", \"unit_price\": 1000}, {\"qty\": 1, \"name\": \"제로콜라\", \"unit_price\": 2300}]'),(11,'2025-11-25 13:04:39',8600,'[{\"qty\": 3, \"name\": \"사이다\", \"unit_price\": 2300}, {\"qty\": 1, \"name\": \"마이쮸\", \"unit_price\": 1000}, {\"qty\": 1, \"name\": \"생수\", \"unit_price\": 700}]'),(12,'2025-12-01 11:27:55',4600,'[{\"qty\": 2, \"name\": \"사이다\", \"unit_price\": 2300}]'),(13,'2025-12-01 11:53:08',7000,'[{\"qty\": 1, \"name\": \"마이쮸\", \"unit_price\": 1000}, {\"qty\": 2, \"name\": \"생수\", \"unit_price\": 700}, {\"qty\": 1, \"name\": \"사이다\", \"unit_price\": 2300}, {\"qty\": 1, \"name\": \"제로콜라\", \"unit_price\": 2300}]'),(14,'2025-12-01 12:04:10',1106300,'[{\"qty\": 2, \"name\": \"사이다\", \"unit_price\": 2300}, {\"qty\": 1, \"name\": \"마이쮸\", \"unit_price\": 1000}, {\"qty\": 1, \"name\": \"생수\", \"unit_price\": 700}, {\"qty\": 1, \"name\": \"휴대폰\", \"unit_price\": 1100000}]'),(15,'2025-12-01 12:21:00',18400,'[{\"qty\": 7, \"name\": \"사이다\", \"unit_price\": 2300}, {\"qty\": 1, \"name\": \"제로콜라\", \"unit_price\": 2300}]'),(16,'2025-12-01 12:24:18',11500,'[{\"qty\": 5, \"name\": \"사이다\", \"unit_price\": 2300}]'),(17,'2025-12-02 13:03:39',6500,'[{\"qty\": 2, \"name\": \"마이쮸\", \"unit_price\": 1000}, {\"qty\": 1, \"name\": \"담배\", \"unit_price\": 4500}]'),(18,'2025-12-02 13:09:41',2000,'[{\"qty\": 2, \"name\": \"마이쮸\", \"unit_price\": 1000}]'),(19,'2025-12-02 13:14:25',5800,'[{\"qty\": 2, \"name\": \"생수\", \"unit_price\": 700}, {\"qty\": 1, \"name\": \"술\", \"unit_price\": 1900}, {\"qty\": 1, \"name\": \"솜사탕\", \"unit_price\": 1500}, {\"qty\": 1, \"name\": \"마이쮸\", \"unit_price\": 1000}]'),(20,'2025-12-02 18:22:10',2000,'[{\"qty\": 1, \"name\": \"빵\", \"unit_price\": 2000}]');
/*!40000 ALTER TABLE `purchase_history` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-05  0:15:08
