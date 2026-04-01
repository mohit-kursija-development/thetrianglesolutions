-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Mar 31, 2026 at 03:35 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.1.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `mahesh_traders`
--
CREATE DATABASE IF NOT EXISTS `mahesh_traders` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `mahesh_traders`;

-- --------------------------------------------------------

--
-- Table structure for table `area_code`
--

CREATE TABLE IF NOT EXISTS `area_code` (
  `code` varchar(3) NOT NULL,
  `area_name` varchar(20) NOT NULL,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `area_code`:
--

--
-- Dumping data for table `area_code`
--

INSERT INTO `area_code` (`code`, `area_name`) VALUES
('', ''),
('AG', 'Asela Gaon'),
('BR', 'Bhatia Road'),
('DG', 'Dhobi Ghat'),
('FM', 'Fish Market'),
('GM', 'Goal Maidan'),
('JB', 'Japani Bazar'),
('KC', 'Kailash Colony'),
('KU', 'Kurla Camp'),
('LC', 'Lal Chaki'),
('SR', 'Shiv Road'),
('ST', 'Subash Tekdi'),
('UK', 'Unknown'),
('VB', 'Vasanshah Bazar'),
('VW', 'Vithalwadi');

-- --------------------------------------------------------

--
-- Table structure for table `orders`
--

CREATE TABLE IF NOT EXISTS `orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `shop_id` int(11) NOT NULL,
  `payment_status` enum('pending','collected') NOT NULL,
  `payment_collected_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_fk` (`user_id`),
  KEY `shop_id` (`shop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `orders`:
--   `shop_id`
--       `shops` -> `id`
--   `user_id`
--       `users` -> `id`
--

--
-- Dumping data for table `orders`
--

INSERT INTO `orders` (`id`, `user_id`, `shop_id`, `payment_status`, `payment_collected_at`, `created_at`) VALUES
(2, 1, 5, 'collected', '2026-03-30 07:17:43', '2026-03-29 13:34:34'),
(3, 1, 1, 'collected', '2026-03-30 08:15:03', '2026-03-29 13:35:20'),
(4, 2, 2, 'collected', '2026-03-30 12:53:45', '2026-03-29 13:37:04'),
(5, 2, 1, 'collected', '2026-03-30 07:41:45', '2026-03-29 14:42:53'),
(6, 2, 3, 'collected', '2026-03-30 10:46:30', '2026-03-29 14:43:00'),
(7, 2, 4, 'pending', '2026-03-30 07:16:00', '2026-03-29 14:43:09'),
(8, 2, 4, 'pending', '2026-03-30 07:16:00', '2026-03-30 05:12:57'),
(9, 2, 1, 'collected', '2026-03-30 07:17:13', '2026-03-30 05:13:17'),
(11, 2, 24, 'pending', '2026-03-30 08:07:50', '2026-03-30 08:07:50'),
(12, 2, 22, 'pending', '2026-03-30 08:07:56', '2026-03-30 08:07:56'),
(13, 2, 1, 'collected', '2026-03-30 08:16:12', '2026-03-30 08:15:23'),
(14, 2, 1, 'collected', '2026-03-30 08:46:20', '2026-03-30 08:15:32'),
(15, 2, 1, 'collected', '2026-03-30 08:16:20', '2026-03-30 08:15:40'),
(16, 2, 1, 'collected', '2026-03-30 08:16:15', '2026-03-30 08:15:49'),
(18, 3, 4, 'collected', '2026-03-30 12:55:34', '2026-03-30 09:13:14'),
(19, 3, 23, 'pending', '2026-03-30 20:27:38', '2026-03-30 20:27:38');

-- --------------------------------------------------------

--
-- Table structure for table `order_items`
--

CREATE TABLE IF NOT EXISTS `order_items` (
  `order_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `price` float NOT NULL,
  KEY `order_id_fk` (`order_id`),
  KEY `product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `order_items`:
--   `order_id`
--       `orders` -> `id`
--   `product_id`
--       `products` -> `id`
--

--
-- Dumping data for table `order_items`
--

INSERT INTO `order_items` (`order_id`, `product_id`, `quantity`, `price`) VALUES
(2, 1, 3, 75),
(2, 2, 10, 75),
(2, 3, 5, 62),
(2, 4, 3, 350),
(3, 3, 3, 62),
(3, 4, 2, 350),
(4, 1, 2, 75),
(5, 1, 10, 75),
(5, 2, 10, 75),
(5, 3, 12, 62),
(5, 4, 3, 350),
(6, 1, 10, 75),
(7, 3, 5, 62),
(8, 1, 11, 75),
(8, 3, 20, 61),
(8, 4, 3, 350),
(9, 1, 5, 75),
(11, 1, 5, 75),
(12, 2, 3, 75),
(13, 1, 10, 75),
(13, 2, 5, 75),
(14, 1, 3, 75),
(14, 2, 10, 75),
(14, 4, 3, 350),
(15, 2, 5, 75),
(15, 3, 3, 62),
(16, 2, 1, 75),
(16, 4, 3, 350),
(18, 1, 10, 78),
(18, 3, 20, 62),
(19, 1, 5, 75),
(19, 2, 3, 75),
(19, 4, 1, 350);

-- --------------------------------------------------------

--
-- Table structure for table `products`
--

CREATE TABLE IF NOT EXISTS `products` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `mrp` float DEFAULT NULL,
  `price` float NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `products`:
--

--
-- Dumping data for table `products`
--

INSERT INTO `products` (`id`, `name`, `mrp`, `price`, `created_at`, `updated_at`) VALUES
(1, 'RAJU GOTA ( WHITE) 1 KG', 150, 75, '2026-03-18 12:39:38', '2026-03-18 12:39:38'),
(2, 'RAJU GOTA ( GREEN) 1 KG', 150, 75, '2026-03-18 12:39:38', '2026-03-18 12:39:38'),
(3, 'RAJU SURF 1 KG', 120, 62, '2026-03-18 13:01:08', '2026-03-18 13:01:08'),
(4, 'RAJU SURF 4 KG', 500, 350, '2026-03-18 13:01:08', '2026-03-18 13:01:08');

-- --------------------------------------------------------

--
-- Table structure for table `shops`
--

CREATE TABLE IF NOT EXISTS `shops` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(300) NOT NULL,
  `address` varchar(300) NOT NULL,
  `area_code` varchar(10) DEFAULT NULL,
  `number_1` varchar(25) DEFAULT NULL,
  `number_2` varchar(25) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `area_code_fk` (`area_code`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `shops`:
--   `area_code`
--       `area_code` -> `code`
--

--
-- Dumping data for table `shops`
--

INSERT INTO `shops` (`id`, `name`, `address`, `area_code`, `number_1`, `number_2`, `created_at`, `updated_at`) VALUES
(1, 'Sheetal Soap Depo', 'Shop no 23, OT section 2, opp Girls School, Ulhasnagar 1', 'GM', '9876543210', '', '2026-03-18 14:50:02', '2026-03-18 14:50:02'),
(2, 'Deepak General Store', 'Shop no 2, OT section 3, opp Girls School, Ulhasnagar 2', 'BR', NULL, NULL, '2026-03-18 14:50:02', '2026-03-18 14:50:02'),
(3, 'Syham kiryana', 'Sadhubella school unr 4', 'JB', NULL, NULL, '2026-03-29 08:30:52', '2026-03-29 08:30:52'),
(4, 'General Store', 'Shop no 2, OT section 3, opp Girls School, Ulhasnagar 3', 'DG', NULL, NULL, '2026-03-18 14:50:02', '2026-03-18 14:50:02'),
(5, 'Pritty Kiryana', 'Shop no 2, OT section 3, opp Girls School, Ulhasnagar 3', 'JB', NULL, NULL, '2026-03-18 14:50:02', '2026-03-18 14:50:02'),
(6, 'Deepak General Store', 'Shop no 2, OT section 3, opp Girls School', '', NULL, NULL, '2026-03-18 14:50:02', '2026-03-18 14:50:02'),
(7, 'Jhulelal Sweets & Farsan', 'Main Road, Near Nehru Chowk', '', NULL, NULL, '2026-03-18 15:30:00', '2026-03-18 15:30:00'),
(8, 'Sai Baba Medical', 'Shop 15, Near Central Hospital', '', NULL, NULL, '2026-03-19 04:00:15', '2026-03-19 04:00:15'),
(9, 'New Selection Cloth Center', 'Gajanan Market, Block A-402', '', NULL, NULL, '2026-03-19 04:45:22', '2026-03-19 04:45:22'),
(10, 'Prince Electronics', 'Opposite Sapna Garden, Shop 5', '', NULL, NULL, '2026-03-19 06:15:10', '2026-03-19 06:15:10'),
(11, 'Bharat Footwear', 'Section 17, Main Bazaar', '', NULL, NULL, '2026-03-19 06:50:00', '2026-03-19 06:50:00'),
(12, 'Krishna Stationery', 'Shop 4, Near Netaji School', '', NULL, NULL, '2026-03-19 08:40:05', '2026-03-19 08:40:05'),
(13, 'National Hardware', 'Gol Maidan, Shop 88', '', NULL, NULL, '2026-03-19 09:30:00', '2026-03-19 09:30:00'),
(14, 'Laxmi Dairy', 'Section 25, Near Shiv Mandir', '', NULL, NULL, '2026-03-19 11:00:45', '2026-03-19 11:00:45'),
(15, 'Standard Bakery', 'Shop 12, Khemani Road', '', NULL, NULL, '2026-03-20 02:30:00', '2026-03-20 02:30:00'),
(16, 'Modern Optical', 'Opposite Railway Station', '', NULL, NULL, '2026-03-20 03:45:00', '2026-03-20 03:45:00'),
(17, 'Choice Collections', 'Dudhnaka, Shop no 7', '', NULL, NULL, '2026-03-20 05:15:12', '2026-03-20 05:15:12'),
(18, 'Raj Mobile Accessories', 'Section 3, Near Lal Chakki', 'ST', '', '', '2026-03-20 06:30:00', '2026-03-20 06:30:00'),
(19, 'Quality Provisions', 'Shop 102, Netaji Market', '', NULL, NULL, '2026-03-20 07:50:30', '2026-03-20 07:50:30'),
(20, 'Evergreen Florist', 'Near Chopra Court', '', NULL, NULL, '2026-03-20 09:10:00', '2026-03-20 09:10:00'),
(21, 'Milan Mens Wear', 'Block 560, Section 28', '', NULL, NULL, '2026-03-21 05:30:00', '2026-03-21 05:30:00'),
(22, 'Super Auto Parts', 'Shop 9, Vitthalwadi Road', '', NULL, NULL, '2026-03-21 07:00:00', '2026-03-21 07:00:00'),
(23, 'Vijay Sports', 'Near Town Hall', '', NULL, NULL, '2026-03-21 08:45:00', '2026-03-21 08:45:00'),
(24, 'Ganesh Toy Shop', 'Section 2, Opp. Municipality Office', '', NULL, NULL, '2026-03-21 10:30:22', '2026-03-21 10:30:22'),
(25, 'Shakti Fertilizers', 'Shop 33, Industrial Area', '', NULL, NULL, '2026-03-21 12:15:00', '2026-03-21 12:15:00'),
(26, 'Mohan Kiryana', 'Lal chaki, shop 23, near yy', NULL, '8888058224', '', '2026-03-31 08:18:33', '2026-03-31 08:18:33');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(30) NOT NULL,
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('sales','admin') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `users`:
--

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `username`, `password`, `role`, `created_at`, `updated_at`) VALUES
(1, 'Hari Ram', 'hariram', 'scrypt:32768:8:1$dPkN7Nt2txAJEn1v$7f816c6934fc51efff513a088a107dc7b80f08e73458359f5dcb2c20384f44570db4014f933129fcda63aa3fa74fb40f9658a32baea985203de66f3b2c9f4ca9', 'sales', '2026-03-18 09:33:11', '2026-03-18 09:33:11'),
(2, 'Lakhan', 'lakhan', 'scrypt:32768:8:1$NnRFSgQXLC6koExd$d4eaf0773241d3357e4eb79c6ea0a0b13f701ef0ea014fdc876e1866ce2b55da1eddbd6e5522e1904dcd08a5bafa3fa0cfe1f799d13118957e1336d21354043a', 'sales', '2026-03-18 09:33:11', '2026-03-18 09:33:11'),
(3, 'Amit', 'amit', 'scrypt:32768:8:1$enKoqjwpqVEsH4ju$2958ce5a45296eb95f73e66fc21f5f27acc633e5c6d6c6fbd3777fecd066b397eb9bd8f8d2b717a10091b1a45bb526b037b0baab4a09c6402529046e9e0404de', 'admin', '2026-03-18 09:33:11', '2026-03-18 09:33:11');

--
-- Constraints for dumped tables
--

--
-- Constraints for table `orders`
--
ALTER TABLE `orders`
  ADD CONSTRAINT `shop_id` FOREIGN KEY (`shop_id`) REFERENCES `shops` (`id`),
  ADD CONSTRAINT `user_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `order_items`
--
ALTER TABLE `order_items`
  ADD CONSTRAINT `order_id_fk` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `product_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

--
-- Constraints for table `shops`
--
ALTER TABLE `shops`
  ADD CONSTRAINT `area_code_fk` FOREIGN KEY (`area_code`) REFERENCES `area_code` (`code`) ON DELETE NO ACTION ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
