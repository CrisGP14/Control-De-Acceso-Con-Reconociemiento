import mysql.connector
#Conexion de la base de datos
con = mysql.connector.connect(host="localhost",user="root",passwd ="", database="almacen_ceti") 
def buscar_todo():
	cur =con.cursor()
	#Consulta
	cur.execute("SELECT * FROM usuarios")
	datos = cur.fetchall()
	cur.close()
	con.close()
	#Mostrar datos
	return datos


def insertar(Nombre, Nivel):
	cur =con.cursor()
	#Consulta
	sql = "INSERT INTO usuarios(usuario, pass, nivel) VALUES ('{}',2,'{}')".format(Nombre,Nivel)
	cur.execute(sql)
	con.commit()
	cur.close()


#mostrar = buscar_todo()
#for fila in mostrar:
#	print(fila)

insertar('Cris',1)
