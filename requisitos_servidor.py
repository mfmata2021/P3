from datetime import datetime
import os


# NOTA: Script de funciones creadas como requisito de la entrega 3 del trabajo final
# Para crear la pila, necesitamos la clase Nodo y la clase Pila


class Nodo: 

    def __init__(self, data = None, siguiente = None):
        self.data = data
        self.siguiente = siguiente

class Pila: 

    def __init__(self):
        self.cima = None #Importante inicializar a 0
        self.tamano = 0

    def apilar(self, data):
        self.cima = Nodo(data=data, siguiente=self.cima)
        self.tamano += 1 


def marcatiempos():
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")


# -- Modificación de la función recibir_json en herramientas_servidor.py para que cumpla los requisitos de la entrega 3

def recibir_json(cliente, usuario, pilas_versiones):
    # Primero nos aseguramos que existe la pila del usuario
    if usuario not in pilas_versiones:
        pilas_versiones[usuario] = Pila()

    pila = pilas_versiones[usuario]

    # Recibir tamaño del JSON
    tamaño_datos = b""
    while b"\n" not in tamaño_datos:
        tamaño_datos += cliente.recv(1)
    tamaño = int(tamaño_datos.decode().strip())

    # Recibir contenido del JSON
    recibido = b""
    while len(recibido) < tamaño:
        recibido += cliente.recv(1024)

    ruta_actual = os.path.join("datos_server", usuario, "biblioteca.json")
    os.makedirs(os.path.dirname(ruta_actual), exist_ok=True)

    if os.path.exists(ruta_actual):
        timestamp = marcatiempos()
        ruta_version = os.path.join(
            "datos_server", usuario, f"biblioteca_{timestamp}.json"
        )

        os.rename(ruta_actual, ruta_version)
        pila.push(ruta_version)


    with open(ruta_actual, "w", encoding="utf-8") as f:
        f.write(recibido.decode())
