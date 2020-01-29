USE testdb;
CREATE TABLE games (title VARCHAR(255), owner VARCHAR(255), playercount VARCHAR(255), game_uuid VARCHAR(255), categories VARCHAR(255), last_played DATE);
USE testdb;
CREATE TABLE settings (user VARCHAR(255), notify_participation TINYINT(1) DEFAULT 1, notify_vote TINYINT(1) DEFAULT 1);
USE testdb;
CREATE TABLE expansions (title VARCHAR(255), owner VARCHAR(255), basegame_uuid VARCHAR(255));
USE testdb;
CREATE TABLE households (user_ids VARCHAR(255)); 
USE testdb;
CREATE TABLE categories(`lang` VARCHAR(255), `kurz` VARCHAR(255), `komplex` VARCHAR(255), `simpel` VARCHAR(255), `Kooperationsspiel` VARCHAR(255), `Partyspiel` VARCHAR(255), `storylastig` VARCHAR(255), `Wuerfelspiel` VARCHAR(255), `Kartenspiel` VARCHAR(255), `Worker Placement` VARCHAR(255), `Resource Management` VARCHAR(255), `Tile Placement` VARCHAR(255), `Deckbuilding` VARCHAR(255), `Drafting` VARCHAR(255), `Social Deduction` VARCHAR(255))