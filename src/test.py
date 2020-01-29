owner = "karacol"
no_participants = 2
column = "title"
table = "games"
category = "Wuerfelspiel"

where = "owner LIKE \'%" + owner + "%\' AND (playercount>=" + str(no_participants) + " OR playercount=\'X\')"
sql = "SELECT (" + column + ", game_uuid) FROM " + table + " AS G WHERE " + where + ";"
sql += "SELECT " + category + " FROM  categories AS C;"
sql += "INNER JOIN games ON G.game_uuid C." + category

print(sql)