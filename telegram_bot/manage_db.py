from time import sleep
import logging

logging.basicConfig(level=logging.INFO)

# Paste the database connection parameters here
host = "1.234.567.89"
port = 12345
user = "root"
password = "1234"
database = "мини-гостиница"

def read(query):
	from mysql.connector import connect
	
	logging.info(f"Запрос: {query}")

	try:
		with connect (
				host = host,
				port = port,
				user = user,
				password = password,
				database = database
			) as connection:

			with connection.cursor(buffered=True) as cursor:

				cursor.execute(query)

				responce = []
				for resp in cursor:
					responce.append(resp)
				return responce

	except Exception as e:
		logging.error(e)

def write(query):
	from mysql.connector import connect
	
	logging.info(f"Запрос: {query}")

	try:
		with connect (
				host = host,
				port = port,
				user = user,
				password = password,
				database = database
			) as connection:

			with connection.cursor(buffered=True) as cursor:

				cursor.execute(query)
				connection.commit()

				responce = []
				for resp in cursor:
					responce.append(resp)
				return responce

	except Exception as e:
		logging.error(e)

def handle(args):
	room_type = args[0]
	date_arr = "-".join(args[1].split(".")[::-1])
	date_dep = "-".join(args[2].split(".")[::-1])
	query = f"""select count(*)
from
(select reserving.date_reserving, reserving.date_departure, p.description
from
(select room.id_room, room_type.description
from room inner join room_type using (id_room_type)) p
inner join reserving using (id_room)
where ((DATEDIFF(reserving.date_reserving, '{date_arr}') >= 0) AND (DATEDIFF(reserving.date_departure, '{date_dep}') <= 0) and (p.description like "%{room_type}%"))) t;"""
	
	n_of_reserved = (read(query))[0][0]

	if room_type == "Двухместный":
		if n_of_reserved <= 7:
			return (True, 8-n_of_reserved)

	if room_type == "Трехместный":
		if n_of_reserved <= 2:
			return (True, 3-n_of_reserved)

	if room_type == "Четырехместный":
		if n_of_reserved <= 3:
			return (True, 4-n_of_reserved)

	return False

def handle_write(args):
	room_type = args[0]
	date_arr = "-".join(args[1].split(".")[::-1])
	date_dep = "-".join(args[2].split(".")[::-1])
	name = args[3]
	phone = args[4]

	query1 = f"""INSERT IGNORE INTO client(full_name, contact_details)
VALUES ('{name}', '{phone}')"""
	write(query1)
	sleep(1)

	query2 = f"""SELECT id_client
FROM client
WHERE (full_name = '{name}' AND contact_details = '{phone}')"""
	resp = read(query2)
	id_client = resp[0][0]

	query3 = f"""select p.id_room
from
    (select room.id_room, room_type.description
        from room inner join room_type using (id_room_type)) p
    inner join reserving using (id_room)
where ((DATEDIFF(reserving.date_reserving, '{date_arr}') >= 0) AND (DATEDIFF(reserving.date_departure, '{date_dep}') <= 0) and (p.description like '%{room_type}%'))"""
	resp = read(query3)
	if room_type == "Двухместный":
		for i in [2, 3, 4, 8, 9, 10, 15, 16]:
			if i not in resp:
				id_room = i
				break
	elif room_type == "Трехместный":
		for i in [5, 11, 17]:
			if i not in resp:
				id_room = i
				break
	elif room_type == "Четырехместный":
		for i in [6, 12, 18]:
			if i not in resp:
				id_room = i
				break

	query4 = f"""INSERT IGNORE INTO reserving(id_client, id_room, id_account, date_reserving, date_departure)
VALUES ('{id_client}', '{id_room}', 11, '{date_arr}', '{date_dep}')"""
	write(query4)