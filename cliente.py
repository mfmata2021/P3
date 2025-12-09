import socket
import pickle
from herramientas_cliente import *
import sys

from app import pedir_int, menu_canciones, menu_listas, menu_reproduccion

ip = sys.argv[1]
puerto = int(sys.argv[2])

# IMPORTANTE RECORDAR!!!! El puerto y la ip se pide por linea de comandos, recordar cambiar !!!
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Creamos el socket 
cliente.connect((ip, puerto)) #Lo conectamos a la dirección IP y al puerto del servidor


"""El cliente pide el nombre de usuario y se conecta al servidor, enviando su 
credencial"""


# Lista de usuarios que tiene el servidor conectado, así podemos comprobar que no se repita el mismo nombre
data = cliente.recv(1024)
usuarios_bloqueados = pickle.loads(data) #Aquí está la lista de usuarios bloqueados que tiene el servidor 

print("\n-- Bienvenido a la biblioteca de música --\n")
print("Antes de iniciar, introduzca un nombre de usuario")

# ------------ INICIO Y CONEXIÓN -------------------------------------
# Bucle para comprobar que no se repita el mismo nombre de usuario
while True: 
    usuario = input("> ").strip()

    if not usuario:
        print("El nombre no puede estar vacío")
        continue

    if usuario not in usuarios_bloqueados:
        comando = "REGISTRO"
        mensaje = comando + ":" + usuario
        print(f"Enviando mensaje al servidor: {mensaje}")
        cliente.sendall(mensaje.encode())
        print("Esperando respuesta del servidor...")
        
        try:
            respuesta = cliente.recv(1024).decode()
            print(f"Respuesta recibida del servidor: {respuesta}")
            if respuesta == "OK":
                print("Usuario conectado")
                break
            elif respuesta == "DENEGADO":
                print("Registro rechazado por el servidor")
                cliente.close()
                exit()
            else:
                print(f"Respuesta inesperada del servidor: {respuesta}")
                cliente.close()
                exit()
        except Exception as e:
            print(f"Error al recibir respuesta del servidor: {e}")
            import traceback
            traceback.print_exc()
            cliente.close()
            exit()
    else:
        print("El nombre de usuario no está disponible. Inténtelo de nuevo")

# ---------- SINCRONIZACIÓN INICIAL Y DESCARGA --------------------------
comando = "SINCRONIZAR"
cliente.sendall(comando.encode()) #Si el servidor responde que OK, el cliente solicita la descarga de su biblioteca
print("\nDescargando biblioteca...\n")
data_json = recibir_json(cliente, usuario)
recibir_mp3(cliente, usuario)
print("Biblioteca descargada y lista para usar")

# ------------- TRABAJO LOCAL -----------------------
plataforma = reconstruir_plataforma(usuario, data_json)

while True:
    print('\n=== Plataforma Musical (TRABAJO LOCAL) ===')
    print('1) Gestionar canciones')
    print('2) Gestionar listas')
    print('3) Reproducción')
    print('0) Salir (Sincronizar y cerrar sesión)')
    
    opc = pedir_int('> ') # Usamos la función pedir_int de app.py

    if opc == 1:
        menu_canciones(plataforma)
    elif opc == 2:
        menu_listas(plataforma)
    elif opc == 3:
        menu_reproduccion(plataforma)
    elif opc == 0:
        print('Fin del trabajo local. Sincronizando...')
        break
    else:
        print('Opción inválida')

# -------------- CIERRE Y SINCRONIZACIÓN FINAL -------------
serializar_plataforma(plataforma, usuario)

cliente.sendall("SUBIR".encode())
enviar_json(cliente, usuario)
enviar_mp3(cliente, usuario)

cliente.sendall("SALIR".encode())
cliente.close()
