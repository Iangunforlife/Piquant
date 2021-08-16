CREATE DATABASE IF NOT EXISTS `Piquant` DEFAULT CHARACTER SET utf8 COLLATE
utf8_general_ci;
USE `Piquant`;

Delimiter $$
create procedure error_handling()
begin
Declare continue handler for 1062
select 'Duplicate keys found';
Declare continue handler for 1064
select 'unknown command'; 

CREATE TABLE IF NOT EXISTS `Menu`(`item_code` varchar(6), `item_name` varchar(50), `item_desc` varchar(300), `item_price` decimal(5,2),
                                    PRIMARY KEY(item_code));

CREATE TABLE IF NOT EXISTS `Cart`(`order_num` varchar(17) NOT NULL,
								  `table_num` varchar(6) NOT NULL, `email` varchar(100) NOT NULL, 
                                   `item_code` varchar(6) NOT NULL, `status` varchar(15),
                                   PRIMARY KEY(`order_num`)
                                   );

CREATE TABLE IF NOT EXISTS `Reservation`(`reservation_id` int(6) NOT NULL AUTO_INCREMENT, `full_name` varchar(50),
										 `email` varchar(100) NOT NULL, `phone_num` varchar(8) NOT NULL,
                                           `reservation_date` date NOT NULL, `reservation_time` time NOT NULL,
                                           `card_name` varchar(50), `card_number` varchar(255) NOT NULL, 
                                           `expiry_date` date NOT NULL, `cvv` varchar(255) NOT NULL,
                                           `additional_note` varchar(100), `encrypt_key` varchar(255) NOT NULL,
                                           PRIMARY KEY(`reservation_id`)) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `Account`(`email` varchar(100) NOT NULL, `full_name` varchar(50),
                                        `password` varchar(255) NOT NULL, `pwd_expiry` date, `account_type` varchar(50),
                                        `phone_num` varchar(8) NOT NULL, `member_level` varchar(30), 
                                        `member_completion` varchar(8), `sign_up_date` date,
                                        `staff_id` varchar(30), `manager_id` varchar(30), `hire_date` date, `job_title` varchar(60),
                                        `account_status` varchar(50),  `2fa_status` varchar(3),
                                        PRIMARY KEY(`email`));
                                       
CREATE TABLE IF NOT EXISTS `Rewards`(`reward_code` varchar(10), `status` varchar(20),
                                         PRIMARY KEY(`reward_code`));      

CREATE TABLE IF NOT EXISTS `Password_Hist`(`serial_no` int NOT NULL AUTO_INCREMENT, `email` varchar(100) NOT NULL, 
										    `password` varchar(255) NOT NULL, 
											PRIMARY KEY(`serial_no`)) ENGINE=InnoDB;   
   
CREATE TABLE IF NOT EXISTS `security_qn`(`email`  varchar(100) NOT NULL, `Security_Question` varchar(200) NOT NULL,
										 `answer` varchar(5) NOT NULL,
                                         PRIMARY KEY(`email`));                                         

CREATE TABLE IF NOT EXISTS `Audit`(`email` varchar(100) NOT NULL, `full_name` varchar(50), `staff_id` varchar(30), `login_time` varchar(200), `logout_time` varchar(200),
`action` varchar(100) DEFAULT 'No action', `failed_login` int(100) DEFAULT 0, `usage` int(100), `role` varchar(50), `suspicious` int(100) default 0,
PRIMARY KEY (`email`),
CONSTRAINT FK_AccountEmail FOREIGN KEY (`email`) references piquant.account(`email`));

-- Create Staff (Inital Password is Hello@01)
insert into piquant.account VALUES('ianwxsim@gmail.com', 'Ian Sim','$2b$16$I6D4efSyAvduOx9vzX5rhOqJB1TOtS6/LY.HWXtd0Ht3qHXcQzj8m', '2021-11-01', 'Staff','87547432', null, null, null, 'Ian', 'Ian', '2021-07-01', 'manager', NULL, NULL);
insert into piquant.audit VALUES('ianwxsim@gmail.com', 'Ian Sim','Ian Sim', null,null,'No action', 0, null, 'Manager', 0);

-- Menu
insert into piquant.menu VALUES ('S001', 'Foie Gras', 'Served with freshly picked goose liver from our own farms, immediately cooked upon ordering for ultimate fresheness.', '12.00');
insert into piquant.menu VALUES ('S002', 'Mushroom Soup', 'Cooked with freshly picked wild mushroom from Brussels and fresh herbs from the hills of Bulgaria.', '6.00');
insert into piquant.menu VALUES ('M001', '150g Wagyu Beef', 'Top-grade Wagyu-beef from Kobe,Japan, Served with sittake mushroom and oven-baked aspargrus.', '75.00');
insert into piquant.menu VALUES ('M002', 'Lobster Risotto', 'Cooked with freshly picked and succlent Lobster from Sweden. Served with fresh Scallops and tobiko.', '40.00');
insert into piquant.menu VALUES ('D001', 'Chocolate Fondle', 'Served with piping hot choclate as well as 15 world famous marshmellow to go with it.', '20.00');
insert into piquant.menu VALUES ('D002', 'Lobster Risotto', 'Prepared with our home-made recipe dough and chocolate. Comes with 5 Pieces.', '15.00');
insert into piquant.menu VALUES ('E001', 'Espresso', 'Made with our fresh arabic coffee beans. Comes in a 350ml jug for your enjoyment.', '10.00');
insert into piquant.menu VALUES ('E002', 'Singapore Mocktail', 'Made with fresh pineapples, watermelon, grape and Apple juice to quench your thirst.', '13.00');
insert into piquant.menu VALUES ('W001', '1992 Wines', 'Freshly imported wines from the USA. Comes in a 350ml bottle.', '70.00');
insert into piquant.menu VALUES ('W002', 'Champagne', 'Freshly imported Champagne from Sweden. Comes in a 300ml bottle.', '90.00');

end $$
Delimiter ;

call error_handling();