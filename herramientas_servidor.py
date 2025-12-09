import os 

#NOTA: Script de funciones creadas como requisito de la entrega 2 del trabajo final 

# Esta función, creará un nuevo directorio para cada usuario nuevo que se conecte
def crear_carpeta(nombre_usuario):
    ruta_usuario = os.path.join("datos_server", nombre_usuario)
    ruta_mp3 = os.path.join(ruta_usuario, "mp3")

    os.makedirs(ruta_mp3, exist_ok=True)
    print(f"Carpetas creadas: {ruta_usuario} / mp3")


def enviar_json(cliente, usuario):

    ruta = os.path.join("datos_server", usuario, "biblioteca.json")

    # Si no existe, crear JSON vacío
    if not os.path.exists(ruta):
        with open(ruta, "w") as f:
            f.write('{"canciones": [], "listas": []}')


    # Leer el contenido del archivo
    with open(ruta, "r") as f:
        texto = f.read()


    # Enviar el tamaño del JSON con newline incluido
    cliente.sendall(str(len(texto)).encode() + b"\n")

    # Enviar el contenido
    cliente.sendall(texto.encode())


def enviar_mp3(cliente, usuario):

    carpeta = os.path.join("datos_server", usuario, "mp3")

    # Crear carpeta si no existe
    if not os.path.exists(carpeta):
        os.mkdir(carpeta)

    # Contar mp3
    archivos = []

    for nombre in os.listdir(carpeta):  # archivos será una lista de strings, donde cada string es el nombre de un archivo o subcarpeta dentro de "mi_carpeta"
        if nombre.endswith(".mp3"):
            archivos.append(nombre)

    # Enviar cuántos mp3 hay
    cliente.sendall(str(len(archivos)).encode() + b"\n")

    # Enviar cada mp3
    for nombre in archivos:
        ruta = os.path.join(carpeta, nombre)

        with open(ruta, "rb") as f:
            datos = f.read()

        # Tamaño del archivo
        cliente.sendall(str(len(datos)).encode() + b"\n")

        # Nombre del archivo
        cliente.sendall(nombre.encode() + b"\n")

        # Datos binarios
        cliente.sendall(datos)


def recibir_json(cliente, usuario):
    # Recibir tamaño del JSON
    tamaño_datos = b""
    while b"\n" not in tamaño_datos:
        tamaño_datos += cliente.recv(1)
    tamaño = int(tamaño_datos.decode().strip())

    # Recibir contenido del JSON
    recibido = b""
    while len(recibido) < tamaño:
        recibido += cliente.recv(1024)

    # Guardar JSON en servidor
    ruta = os.path.join("datos_server", usuario, "biblioteca.json")
    with open(ruta, "w") as f:
        f.write(recibido.decode())


def recibir_mp3(cliente, usuario):
    carpeta = os.path.join("datos_server", usuario, "mp3")
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    # Número de archivos
    num_archivos_datos = b""
    while b"\n" not in num_archivos_datos:
        num_archivos_datos += cliente.recv(1)
    num_archivos = int(num_archivos_datos.decode().strip())

    for _ in range(num_archivos):
        # Tamaño del archivo
        tamaño_datos = b""
        while b"\n" not in tamaño_datos:
            tamaño_datos += cliente.recv(1)
        tamaño = int(tamaño_datos.decode().strip())

        # Nombre del archivo
        nombre_datos = b""
        while b"\n" not in nombre_datos:
            nombre_datos += cliente.recv(1)
        nombre = nombre_datos.decode().strip()

        # Recibir datos
        recibido = b""
        while len(recibido) < tamaño:
            recibido += cliente.recv(1024)

        # Guardar archivo
        ruta_archivo = os.path.join(carpeta, nombre)
        with open(ruta_archivo, "wb") as f:
            f.write(recibido)