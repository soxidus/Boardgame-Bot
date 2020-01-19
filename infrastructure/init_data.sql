USE testdb;
CREATE TABLE games (title VARCHAR(255), owner VARCHAR(255), playercount VARCHAR(255), game_uuid VARCHAR(255), categories VARCHAR(255), last_played DATE);
CREATE TABLE settings (user VARCHAR(255), notify_participation BIT(1) DEFAULT 1, notify_vote BIT(1) DEFAULT 1);
CREATE TABLE expansions (title VARCHAR(255), owner VARCHAR(255), basegame_uuid VARCHAR(255));
CREATE TABLE households (user_ids VARCHAR(255));