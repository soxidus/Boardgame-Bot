USE testdb;
CREATE TABLE games (title VARCHAR(255), owner VARCHAR(255), playercount VARCHAR(255), game_uuid VARCHAR(255), last_played DATE);
USE testdb;
CREATE TABLE settings (user VARCHAR(255), notify_participation TINYINT(1) DEFAULT 1, notify_vote TINYINT(1) DEFAULT 1);
USE testdb;
CREATE TABLE expansions (title VARCHAR(255), owner VARCHAR(255), basegame_uuid VARCHAR(255));
USE testdb;
CREATE TABLE households (user_ids VARCHAR(255));
