
-- ---
-- Globals
-- ---

-- SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
-- SET FOREIGN_KEY_CHECKS=0;

-- ---
-- Table 'users'
-- 
-- ---

DROP TABLE IF EXISTS `users`;
		
CREATE TABLE `users` (
  `id` INTEGER(11) NOT NULL AUTO_INCREMENT DEFAULT NULL,
  `username` VARCHAR(30) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  `email` VARCHAR(45) NULL DEFAULT NULL,
  `team_id` INTEGER(11) NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- ---
-- Table 'teams'
-- 
-- ---

DROP TABLE IF EXISTS `teams`;
		
CREATE TABLE `teams` (
  `id` INTEGER NULL AUTO_INCREMENT DEFAULT NULL,
  `name` VARCHAR(255) NOT NULL AUTO_INCREMENT,
  `description` text COLLATE utf8_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- ---
-- Table 'puzzles'
-- 
-- ---

DROP TABLE IF EXISTS `puzzles`;
		
CREATE TABLE `puzzles` (
  `id` INTEGER NULL AUTO_INCREMENT DEFAULT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` text COLLATE utf8_unicode_ci NULL DEFAULT NULL,
  `flag` VARCHAR(255) NULL DEFAULT NULL,
  `is_open` TINYINT(4) NULL DEFAULT NULL,
  `category_id` INTEGER(11) NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- ---
-- Table 'log_submit_flags'
-- 
-- ---

DROP TABLE IF EXISTS `log_submit_flags`;
		
CREATE TABLE `log_submit_flags` (
  `id` INTEGER NOT NULL AUTO_INCREMENT DEFAULT NULL,
  `user_id` INTEGER(11) NOT NULL DEFAULT NULL,
  `puzzle_id` INTEGER(11) NOT NULL DEFAULT NULL,
  `team_id` INTEGER(11) NULL DEFAULT NULL,
  `flag` text COLLATE utf8_unicode_ci NULL DEFAULT NULL,
  `created_at` DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- ---
-- Table 'hints'
-- 
-- ---

DROP TABLE IF EXISTS `hints`;
		
CREATE TABLE `hints` (
  `id` INTEGER NULL AUTO_INCREMENT DEFAULT NULL,
  `puzzle_id` INTEGER(11) NOT NULL DEFAULT NULL,
  `content` text COLLATE utf8_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- ---
-- Table 'categories'
-- 
-- ---

DROP TABLE IF EXISTS `categories`;
		
CREATE TABLE `categories` (
  `id` INTEGER NULL AUTO_INCREMENT DEFAULT NULL,
  `name` VARCHAR(255) NULL DEFAULT NULL,
  `explain` text COLLATE utf8_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- ---
-- Foreign Keys 
-- ---

ALTER TABLE `users` ADD FOREIGN KEY (team_id) REFERENCES `teams` (`id`);
ALTER TABLE `puzzles` ADD FOREIGN KEY (category_id) REFERENCES `categories` (`id`);
ALTER TABLE `log_submit_flags` ADD FOREIGN KEY (user_id) REFERENCES `users` (`id`);
ALTER TABLE `log_submit_flags` ADD FOREIGN KEY (puzzle_id) REFERENCES `puzzles` (`id`);
ALTER TABLE `log_submit_flags` ADD FOREIGN KEY (team_id) REFERENCES `teams` (`id`);
ALTER TABLE `hints` ADD FOREIGN KEY (puzzle_id) REFERENCES `puzzles` (`id`);

-- ---
-- Table Properties
-- ---

-- ALTER TABLE `users` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `teams` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `puzzles` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `log_submit_flags` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `hints` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `categories` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

-- ---
-- Test Data
-- ---

-- INSERT INTO `users` (`id`,`username`,`password`,`email`,`team_id`) VALUES
-- ('','','','','');
-- INSERT INTO `teams` (`id`,`name`,`description`) VALUES
-- ('','','');
-- INSERT INTO `puzzles` (`id`,`name`,`description`,`flag`,`is_open`,`category_id`) VALUES
-- ('','','','','','');
-- INSERT INTO `log_submit_flags` (`id`,`user_id`,`puzzle_id`,`team_id`,`flag`,`created_at`) VALUES
-- ('','','','','','');
-- INSERT INTO `hints` (`id`,`puzzle_id`,`content`) VALUES
-- ('','','');
-- INSERT INTO `categories` (`id`,`name`,`explain`) VALUES
-- ('','','');

--- CREATE USER 'ctf_admin'@'localhost' IDENTIFIED BY 'ctf_admin';
--- CREATE DATABASE ctf CHARACTER SET utf8;
--- GRANT ALL ON ctf.* to ctf_admin@localhost;
--- FLUSH PRIVILEGES;
