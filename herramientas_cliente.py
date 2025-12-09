import os 
import json
from plataforma import PlataformaMusical, Cancion, ListaReproduccion


def recibir_json(cliente, usuario):
    # Recibir tamaño del JSON
    tamaño_datos = b""
    while b"\n" not in tamaño_datos:
        tamaño_datos += cliente.recv(1)
    tamaño = int(tamaño_datos.decode().strip())

    # Recibir contenido del JSON
    recibido = b""
    while len(recibido) < tamaño:
        chunk = cliente.recv(1024)
        recibido += chunk

    # Convertir de bytes a texto
    texto = recibido.decode()

    # Guardar localmente
    ruta_local = os.path.join("datos_cliente", usuario)
    if not os.path.exists(ruta_local):
        os.makedirs(ruta_local)
    with open(os.path.join(ruta_local, "biblioteca.json"), "w") as f:
        f.write(texto)

    # Devolver contenido JSON como dict
    return json.loads(texto)


def recibir_mp3(cliente, usuario):
    # Carpeta local donde guardar mp3
    carpeta = os.path.join("datos_cliente", usuario, "mp3")
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    # Recibir número de archivos
    num_archivos_datos = b""
    while b"\n" not in num_archivos_datos:
        num_archivos_datos += cliente.recv(1)
    num_archivos = int(num_archivos_datos.decode().strip())

    for _ in range(num_archivos):
        # Recibir tamaño del archivo
        tamaño_datos = b""
        while b"\n" not in tamaño_datos:
            tamaño_datos += cliente.recv(1)
        tamaño = int(tamaño_datos.decode().strip())

        # Recibir nombre del archivo
        nombre_datos = b""
        while b"\n" not in nombre_datos:
            nombre_datos += cliente.recv(1)
        nombre = nombre_datos.decode().strip()

        # Recibir datos
        recibido = b""
        while len(recibido) < tamaño:
            chunk = cliente.recv(1024)
            recibido += chunk

        # Guardar archivo
        with open(os.path.join(carpeta, nombre), "wb") as f:
            f.write(recibido)


def enviar_json(cliente, usuario):
    ruta = os.path.join("datos_cliente", usuario, "biblioteca.json")
    with open(ruta, "r") as f:
        texto = f.read()

    cliente.sendall(str(len(texto)).encode() + b"\n")
    cliente.sendall(texto.encode())


def enviar_mp3(cliente, usuario):
    carpeta = os.path.join("datos_cliente", usuario, "mp3")
    
    # Crear carpeta si no existe
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".mp3")]

    # Número de archivos
    cliente.sendall(str(len(archivos)).encode() + b"\n")

    for nombre in archivos:
        ruta = os.path.join(carpeta, nombre)
        with open(ruta, "rb") as f:
            datos = f.read()

        cliente.sendall(str(len(datos)).encode() + b"\n")
        cliente.sendall(nombre.encode() + b"\n")
        cliente.sendall(datos)


def reconstruir_plataforma(usuario, data_json):
    plataforma = PlataformaMusical()

    # Reconstruir canciones
    for c in data_json["canciones"]:
        # Obtener la ruta correcta del archivo (puede venir como 'archivo_mp3' o 'archivo')
        archivo = c.get("archivo_mp3") or c.get("archivo")
        if archivo and not os.path.isabs(archivo):
            # Si la ruta no es absoluta, construirla correctamente
            ruta_archivo = os.path.join("datos_cliente", usuario, "mp3", os.path.basename(archivo))
        else:
            ruta_archivo = archivo
        
        # Verificar que el archivo existe antes de añadirlo
        if ruta_archivo and os.path.exists(ruta_archivo):
            cancion = Cancion(
                c["id"], c["titulo"], c["artista"], c["duracion"], c["genero"], ruta_archivo
            )
            plataforma.canciones.append(cancion)
        else:
            print(f"Advertencia: No se encontró el archivo de la canción '{c['titulo']}' en {ruta_archivo}")

    # Reconstruir listas
    for l in data_json["listas"]:
        lista = ListaReproduccion(l["nombre"])
        lista.canciones = l["canciones"]
        plataforma.listas.append(lista)

    return plataforma

# <--- FUNCIÓN AÑADIDA OBLIGATORIA PARA EL MODELO DE SINCRONIZACIÓN --->
def serializar_plataforma(plataforma, usuario):
    """Serializa el objeto PlataformaMusical modificado al JSON local."""
    
    # Crear lista de canciones con estructura consistente
    canciones_data = []
    for c in plataforma.canciones:
        # Extraer solo el nombre del archivo para guardarlo en JSON
        archivo_nombre = os.path.basename(c.archivo_mp3) if c.archivo_mp3 else ""
        canciones_data.append({
            "id": c.id,
            "titulo": c.titulo,
            "artista": c.artista,
            "duracion": c.duracion,
            "genero": c.genero,
            "archivo_mp3": archivo_nombre
        })
    
    data = {
        "canciones": canciones_data,
        "listas": [
            {
                "nombre": l.nombre,
                "canciones": l.canciones 
            }
            for l in plataforma.listas
        ]
    }
    
    # Guarda el diccionario en el archivo JSON local del usuario
    ruta_local = os.path.join("datos_cliente", usuario)
    if not os.path.exists(ruta_local):
        os.makedirs(ruta_local)
        
    with open(os.path.join(ruta_local, "biblioteca.json"), "w") as f:
        json.dump(data, f, indent=4)
