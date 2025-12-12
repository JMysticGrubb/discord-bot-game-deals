BEGIN TRANSACTION;
DROP TABLE IF EXISTS "game";
CREATE TABLE "game" (
	"game_id"	INTEGER,
	"title"	TEXT,
	"description"	TEXT,
	"developer"	TEXT,
	"publisher"	TEXT,
	PRIMARY KEY("game_id")
);
DROP TABLE IF EXISTS "game_price";
CREATE TABLE "game_price" (
	"price_id"	INTEGER,
	"game_id"	INTEGER,
	"price"	NUMERIC,
	"currency"	TEXT,
	"is_on_sale"	INTEGER CHECK("is_on_sale" IN (0, 1)),
	"end_date"	TEXT,
	PRIMARY KEY("price_id" AUTOINCREMENT),
	FOREIGN KEY("game_id") REFERENCES "game"("game_id") ON DELETE CASCADE ON UPDATE CASCADE
);
DROP TABLE IF EXISTS "game_rating";
CREATE TABLE "game_rating" (
	"rating_id"	INTEGER,
	"game_id"	INTEGER,
	"monthly_rating"	REAL,
	"all_rating"	REAL,
	"scrape_date"	TEXT,
	PRIMARY KEY("rating_id" AUTOINCREMENT),
	FOREIGN KEY("game_id") REFERENCES "game"("game_id") ON DELETE CASCADE ON UPDATE CASCADE
);
DROP TABLE IF EXISTS "game_tag";
CREATE TABLE "game_tag" (
	"game_id"	INTEGER,
	"tag_id"	INTEGER,
	FOREIGN KEY("game_id") REFERENCES "game"("game_id") ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY("tag_id") REFERENCES "tag"("tag_id") ON DELETE CASCADE ON UPDATE CASCADE
);
DROP TABLE IF EXISTS "tag";
CREATE TABLE "tag" (
	"tag_id"	INTEGER,
	"tag_name"	TEXT,
	PRIMARY KEY("tag_id" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "user";
CREATE TABLE "user" (
	"discord_id"	INTEGER,
	"first_seen"	TEXT,
	"last_online"	TEXT,
	"playstyle"	TEXT CHECK("playstyle" IN ("casual", "competitive", "mix")),
	PRIMARY KEY("discord_id")
);
DROP TABLE IF EXISTS "user_activity";
CREATE TABLE "user_activity" (
	"activity_id"	INTEGER,
	"discord_id"	INTEGER,
	"game_id"	INTEGER,
	"activity_type"	TEXT CHECK("activity_type" IN ("playing", "completed", "dropped")),
	"rating"	INTEGER CHECK("rating" IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)),
	"timestamp"	TEXT,
	PRIMARY KEY("activity_id" AUTOINCREMENT),
	FOREIGN KEY("discord_id") REFERENCES "user"("discord_id") ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY("game_id") REFERENCES "game"("game_id") ON DELETE CASCADE ON UPDATE CASCADE
);
COMMIT;
