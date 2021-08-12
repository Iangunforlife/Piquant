CREATE DATABASE IF NOT EXISTS `Piquant` DEFAULT CHARACTER SET utf8 COLLATE
utf8_general_ci;
USE `Piquant`;

CREATE TABLE IF NOT EXISTS `Menu`(`item_code` varchar(5) NOT NULL, item_name varchar(50) NOT NULL, item_desc varchar(300), item_price decimal(5,2) NOT NULL,
                                    PRIMARY KEY(item_code));

CREATE TABLE IF NOT EXISTS `Cart`(`order_num` varchar(17) NOT NULL,
								  `table_num` varchar(6) NOT NULL, `email` varchar(100) NOT NULL, 
                                   `item_code` varchar(6) NOT NULL, `status` varchar(15),
                                   PRIMARY KEY(`order_num`)
                                   );

CREATE TABLE IF NOT EXISTS `Reservation`(`reservation_id` int(6) NOT NULL AUTO_INCREMENT, `full_name` varchar(50),
										 `email` varchar(100) NOT NULL, `phone_num` varchar(8) NOT NULL,
                                           `reservation_date` date NOT NULL, `reservation_time` time NOT NULL,
                                           `card_name` varchar(50), `card_number` varchar(16) NOT NULL, 
                                           `expiry_date` date NOT NULL, `cvv` varchar(3) NOT NULL,
                                           `additional_note` varchar(100),
                                           PRIMARY KEY(`reservation_id`)) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `Account`(`email` varchar(100) NOT NULL, `full_name` varchar(50),
                                        `password` varchar(255) NOT NULL, `account_type` varchar(50),
                                        `phone_num` varchar(8) NOT NULL, `member_level` varchar(30), 
                                        `member_completion` varchar(8), `sign_up_date` date,
                                        `staff_id` varchar(7),  `hire_date` date, `job_title` varchar(60),
                                        PRIMARY KEY(`email`)) ;
                                       
CREATE TABLE IF NOT EXISTS `Rewards`(`reward_code` varchar(10), `status` varchar(20),
                                         PRIMARY KEY(`reward_code`));         
-- new
CREATE TABLE IF NOT EXISTS `Password_Hist`(`serial_no` int NOT NULL AUTO_INCREMENT, `email` varchar(100) NOT NULL, 
										    `password` varchar(255) NOT NULL, 
											PRIMARY KEY(`serial_no`)) ENGINE=InnoDB;   
   
CREATE TABLE IF NOT EXISTS `security_qn`(`email`  varchar(100) NOT NULL, `Security_Question` varchar(200) NOT NULL,
										 `answer` varchar(5) NOT NULL,
                                         PRIMARY KEY(`email`));     
			


