import socket
import threading
import pickle
from herramientas_servidor import *
from requisitos_servidor import *
import sys

#Biblioteca vacía para ir guardando los usuarios y su pila
pila_versiones = {} #esto tendrá la forma { "Usuario" : Pila()}

# Biblioteca que contendrá a los {"usuario" : usuario_socket} que se conecten al servidor y que no pueden ser usuados por nuevos clientes s
usuarios_activos = []
# Para poder modificar variables globales y evitar condiciones de carrera, usamos el lock
lock = threading.Lock()
puerto = int(sys.argv[1])

# IMPORTANTE RECORDAR!!!! EL puerto se pide por linea de comandos, recordar cambiar !!!
print("\nArrancando servidor...")
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((socket.gethostname(), puerto))
servidor.listen()


def comunicacion (cliente, addr):

    global usuarios_activos
    global pila_versiones
    usuario = None

    if cliente:
        print(f"Cliente conectado en: {addr}")
        # -- Envío al cliente la lista de usuarios activos en el servidor
        lock.acquire()
        data = pickle.dumps(usuarios_activos)
        lock.release()
        cliente.sendall(data)


        try:
            while True:

                # IMPORTANTE:Si un hilo puede modificar la lista, entonces todas las lecturas deben protegerse también

                # -- Nos "comunicamos" con el cliente por medio de comandos, dependiendo de lo que nos diga, vamos haciendo x tareas en el servidor

                try:
                    mensaje = cliente.recv(1024) #Aquí llegaría el comando 
                    if not mensaje:
                        break

                    mensaje_decodificado = mensaje.decode()
                    print(f"Servidor recibió: {mensaje_decodificado}")
                    comando = mensaje_decodificado.split(":")
                    
                    if len(comando) < 1:
                        print(f"Error: Mensaje vacío recibido")
                        continue
                    
                    if len(comando) < 2 and comando[0] != "SINCRONIZAR" and comando[0] != "SUBIR" and comando[0] != "SALIR":
                        print(f"Error: Formato de mensaje inválido: {mensaje_decodificado}")
                        continue

                    if comando[0] == "REGISTRO":
                        if len(comando) < 2:
                            print("Error: Comando REGISTRO sin nombre de usuario")
                            cliente.sendall("ERROR".encode())
                            continue
                        usuario = comando[1]
                        print(f"Procesando registro para usuario: {usuario}")

                        lock.acquire()
                        try:
                            if usuario not in usuarios_activos:
                                usuarios_activos.append(usuario)
                                # Crear carpeta solo si no existe (esto permite reconexiones)
                                crear_carpeta(usuario)
                                respuesta = 'OK'
                                print(f"Usuario {usuario} registrado/conectado correctamente")
                            else:
                                respuesta = "DENEGADO"
                                print(f"Usuario {usuario} ya está conectado, registro denegado")
                        finally:
                            lock.release()
                        print(f"Enviando respuesta: {respuesta}")
                        cliente.sendall(respuesta.encode())

                    # ------------------ SINCRONIZACIÓN INICIAL Y DESCARGA ---------------------------
                    elif comando[0] == "SINCRONIZAR" and usuario:
                        enviar_json(cliente, usuario)
                        enviar_mp3(cliente, usuario)

                    elif comando[0] == "SUBIR" and usuario:
                        try:
                            lock.acquire()
                            recibir_json(cliente, usuario, pila_versiones)
                        finally:
                            lock.release()

                        recibir_mp3(cliente, usuario)

                    elif comando[0] == "SALIR":
                        break  # Salir del bucle del hilo
                    else:
                        print(f"Comando desconocido o usuario no registrado: {comando[0]}")
                        
                except Exception as e:
                    print(f"Error al procesar mensaje: {e}")
                    import traceback
                    traceback.print_exc()
                    break

        finally:
            if usuario:
                lock.acquire()
                if usuario in usuarios_activos:
                    usuarios_activos.remove(usuario)
                lock.release()
            cliente.close()
            print(f"Usuario {usuario} liberado y conexión cerrada")
# Esperamos a clientes infinitamente a menos que se interrumpa por teclado
try:
    while True: 
        # Espera a que llegue un nuevo cliente
        cliente, addr = servidor.accept() 


        # Establecida la conexión, crear un objeto hilo para atender al cliente
        # - target: nombre de la función que ejecuta el hilo (sin paréntesis)
        # - args: tupla con los argumentos de la función     
        hilo = threading.Thread(target=comunicacion, args=(cliente, addr))

        #Lanzar el hilo
        hilo.start()

except KeyboardInterrupt:  # Captura la señal generada por Ctrl+C
    servidor.close()  # Cierra el socket del servidor
    print("Apagando servidor...")
