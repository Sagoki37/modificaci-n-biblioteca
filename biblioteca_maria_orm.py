import os
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError, IntegrityError
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de la Base de Datos (Variables de Entorno) ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# Se utiliza el driver mysqlconnector para MariaDB/MySQL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
Base = declarative_base()
ESTADOS_LECTURA = ('Leído', 'No leído')

# --- 1. Definición del Modelo (ORM) ---
class Libro(Base):
    """Define la tabla 'libros' y su mapeo ORM."""
    __tablename__ = 'libros'

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    autor = Column(String(255), nullable=False)
    genero = Column(String(100))
    estado = Column(String(20), nullable=False)

    def __repr__(self):
        return f"<Libro(id={self.id}, titulo='{self.titulo}', autor='{self.autor}', estado='{self.estado}')>"
    
    def to_dict(self):
        """Convierte el objeto Libro en un diccionario para la interfaz CLI."""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'autor': self.autor,
            'genero': self.genero,
            'estado': self.estado
        }

# --- 2. Clase de Gestión de Base de Datos (DBManager) ---
class LibroDBManager:
    """Gestiona la conexión y las operaciones CRUD usando SQLAlchemy."""
    def __init__(self):
        try:
            # Crear el motor de la base de datos
            self.engine = create_engine(DATABASE_URL)
            # Crear las tablas si no existen (similar a _crear_tabla en SQLite)
            Base.metadata.create_all(self.engine)
            # Crear una clase Session que será una fábrica de sesiones
            Session = sessionmaker(bind=self.engine)
            # Crear una sesión activa
            self.session = Session()
            print(" Conexión a MariaDB/SQLAlchemy establecida correctamente.")
        except OperationalError as e:
            print(f" Error de conexión con MariaDB. Revise la cadena de conexión o si el servidor está activo.")
            print(f"Detalle del error: {e}")
            exit()
        except Exception as e:
            print(f" Error inesperado durante la inicialización de la DB: {e}")
            exit()
            
    def __del__(self):
        """Cierra la sesión de SQLAlchemy al destruir el objeto."""
        if self.session:
            self.session.close()

    def insertar_libro(self, titulo, autor, genero, estado):
        """Agrega un nuevo libro (CREATE)."""
        nuevo_libro = Libro(titulo=titulo, autor=autor, genero=genero, estado=estado)
        try:
            self.session.add(nuevo_libro)
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
            return False

    def obtener_todos_los_libros(self):
        """Devuelve todos los libros (READ)."""
        # SQLAlchemy 2.0 style select
        stmt = select(Libro).order_by(Libro.titulo)
        return [libro.to_dict() for libro in self.session.scalars(stmt).all()]

    def obtener_libro_por_id(self, libro_id):
        """Devuelve un libro específico por su ID."""
        return self.session.get(Libro, libro_id)
    
    def actualizar_libro(self, libro_id, campo, nuevo_valor):
        """Actualiza un campo específico de un libro (UPDATE)."""
        libro = self.obtener_libro_por_id(libro_id)
        if not libro:
            return False, "Libro no encontrado."

        try:
            # Se usa setattr para actualizar el atributo del objeto ORM dinámicamente
            setattr(libro, campo, nuevo_valor)
            self.session.commit()
            return True, None
        except Exception as e:
            self.session.rollback()
            return False, f"Error al actualizar: {e}"

    def eliminar_libro(self, libro_id):
        """Elimina un libro por su ID (DELETE)."""
        libro = self.obtener_libro_por_id(libro_id)
        if not libro:
            return False

        try:
            self.session.delete(libro)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False

    def buscar_libros(self, termino):
        """Busca libros por título, autor o género (READ con filtro)."""
        # Uso de .ilike() para búsquedas case-insensitive, si el motor lo soporta
        termino_busqueda = f"%{termino}%"
        stmt = (
            select(Libro)
            .filter(
                (Libro.titulo.ilike(termino_busqueda)) | 
                (Libro.autor.ilike(termino_busqueda)) | 
                (Libro.genero.ilike(termino_busqueda))
            )
            .order_by(Libro.titulo)
        )
        return [libro.to_dict() for libro in self.session.scalars(stmt).all()]

# --- 3. Lógica de la Interfaz de Usuario (CLI) (Adaptada) ---
# Se reutiliza la lógica de CLI de la versión anterior,
# solo se cambia la clase de base de datos usada (db)

def limpiar_pantalla():
    """Limpia la consola."""
    os.system('cls' if os.name == 'nt' else 'clear') 

def mostrar_menu():
    """Muestra el menú de opciones."""
    print("\n" + "="*50)
    print(" Administrador de Biblioteca (MariaDB + SQLAlchemy)")
    print("="*50)
    print("1.  Agregar nuevo libro")
    print("2.  Ver listado de libros")
    print("3.  Buscar libros")
    print("4.  Actualizar información de un libro")
    print("5.  Eliminar libro existente")
    print("6.  Salir")
    print("="*50)

def obtener_entrada(prompt):
    """Obtiene una entrada de texto y asegura que no esté vacía."""
    while True:
        entrada = input(prompt).strip()
        if entrada:
            return entrada
        print(" La entrada no puede estar vacía. Intente de nuevo.")

def obtener_id_valido(db, mensaje):
    """Pide un ID de libro y verifica que exista."""
    while True:
        try:
            libro_id = int(obtener_entrada(mensaje))
            if db.obtener_libro_por_id(libro_id):
                return libro_id
            else:
                print(f" No se encontró ningún libro con el ID {libro_id}.")
        except ValueError:
            print(" Por favor, ingrese un número entero válido para el ID.")

def manejar_agregar_libro(db):
    """Funcionalidad: Agregar nuevo libro."""
    limpiar_pantalla()
    print("\n---  AGREGAR NUEVO LIBRO ---")
    titulo = obtener_entrada("Título: ")
    autor = obtener_entrada("Autor: ")
    genero = obtener_entrada("Género: ")
    
    while True:
        estado_input = obtener_entrada(f"Estado de lectura (1: Leído, 2: No leído): ")
        if estado_input == '1':
            estado = ESTADOS_LECTURA[0] 
            break
        elif estado_input == '2':
            estado = ESTADOS_LECTURA[1] 
            break
        else:
            print(" Opción de estado no válida. Use '1' o '2'.")

    if db.insertar_libro(titulo, autor, genero, estado):
        print(f"\n Libro '{titulo}' de {autor} agregado exitosamente.")
    else:
        print("\n Error al agregar el libro (posible duplicado o error de integridad).")

def mostrar_libros_tabla(libros):
    """Muestra la lista de libros en formato de tabla legible."""
    if not libros:
        print("\n No hay libros registrados o no se encontraron resultados.")
        return

    # Definir anchos máximos para las columnas
    COL_ID = 5
    COL_TITULO = 40
    COL_AUTOR = 25
    COL_GENERO = 15
    COL_ESTADO = 12

    def separador(char='-'):
        return f"+{char*COL_ID}+{char*COL_TITULO}+{char*COL_AUTOR}+{char*COL_GENERO}+{char*COL_ESTADO}+"

    print(separador())
    print(f"| {'ID':<{COL_ID-1}} | {'TÍTULO':<{COL_TITULO-1}} | {'AUTOR':<{COL_AUTOR-1}} | {'GÉNERO':<{COL_GENERO-1}} | {'ESTADO':<{COL_ESTADO-1}} |")
    print(separador('='))

    for libro in libros:
        titulo = (libro['titulo'][:COL_TITULO-3] + '...') if len(libro['titulo']) > COL_TITULO else libro['titulo']
        autor = (libro['autor'][:COL_AUTOR-3] + '...') if len(libro['autor']) > COL_AUTOR else libro['autor']
        genero = (libro['genero'][:COL_GENERO-3] + '...') if len(libro['genero']) > COL_GENERO else libro['genero']

        print(f"| {libro['id']:<{COL_ID-1}} | {titulo:<{COL_TITULO-1}} | {autor:<{COL_AUTOR-1}} | {genero:<{COL_GENERO-1}} | {libro['estado']:<{COL_ESTADO-1}} |")

    print(separador())

def manejar_listado_libros(db):
    """Funcionalidad: Ver listado de libros."""
    limpiar_pantalla()
    print("\n---  LISTADO COMPLETO DE LIBROS ---")
    libros = db.obtener_todos_los_libros()
    mostrar_libros_tabla(libros)

def manejar_buscar_libros(db):
    """Funcionalidad: Buscar libros por título, autor o género."""
    limpiar_pantalla()
    print("\n---  BUSCAR LIBROS ---")
    termino = obtener_entrada("Ingrese el término de búsqueda (título, autor o género): ")
    
    libros = db.buscar_libros(termino)
    
    print(f"\nResultados de la búsqueda para: '{termino}'")
    mostrar_libros_tabla(libros)

def manejar_actualizar_libro(db):
    """Funcionalidad: Actualizar información de un libro."""
    limpiar_pantalla()
    print("\n---  ACTUALIZAR LIBRO ---")
    
    libros = db.obtener_todos_los_libros()
    mostrar_libros_tabla(libros)
    
    if not libros:
        return

    libro_id = obtener_id_valido(db, "\nIngrese el ID del libro a actualizar: ")

    print("\n¿Qué campo desea actualizar?")
    print("1. Título")
    print("2. Autor")
    print("3. Género")
    print("4. Estado de lectura")
    
    opcion = obtener_entrada("Seleccione una opción (1-4): ")

    campos = {'1': 'titulo', '2': 'autor', '3': 'genero', '4': 'estado'}

    if opcion in campos:
        campo_a_actualizar = campos[opcion]
        
        if campo_a_actualizar == 'estado':
            while True:
                nuevo_valor_input = obtener_entrada(f"Nuevo estado (1: Leído, 2: No leído): ")
                if nuevo_valor_input == '1':
                    nuevo_valor = ESTADOS_LECTURA[0]
                    break
                elif nuevo_valor_input == '2':
                    nuevo_valor = ESTADOS_LECTURA[1]
                    break
                else:
                    print(" Opción no válida. Use '1' o '2'.")
        else:
            nuevo_valor = obtener_entrada(f"Ingrese el nuevo valor para '{campo_a_actualizar.capitalize()}': ")
        
        exito, error = db.actualizar_libro(libro_id, campo_a_actualizar, nuevo_valor)
        
        if exito:
            print(f"\n Libro ID {libro_id} actualizado exitosamente.")
        elif error:
            print(f"\n No se pudo actualizar el libro: {error}")
        else:
            print(f"\n No se realizó ninguna actualización.")
    else:
        print(" Opción no válida.")

def manejar_eliminar_libro(db):
    """Funcionalidad: Eliminar libro existente."""
    limpiar_pantalla()
    print("\n---  ELIMINAR LIBRO ---")

    libros = db.obtener_todos_los_libros()
    mostrar_libros_tabla(libros)
    
    if not libros:
        return

    libro_id = obtener_id_valido(db, "\nIngrese el ID del libro a eliminar: ")
    
    confirmacion = input(f" ¿Está seguro que desea eliminar el libro ID {libro_id}? (s/N): ").lower()
    
    if confirmacion == 's':
        if db.eliminar_libro(libro_id):
            print(f"\n Libro ID {libro_id} eliminado exitosamente.")
        else:
            print("\n Error al eliminar el libro o el ID no existe.")
    else:
        print("\nOperación de eliminación cancelada.")


def main():
    """Función principal que ejecuta la aplicación CLI."""
    db = LibroDBManager() # Instancia la clase con SQLAlchemy
    
    while True:
        mostrar_menu()
        
        opcion = input("Seleccione una opción (1-6): ").strip()
        
        if opcion == '1':
            manejar_agregar_libro(db)
        elif opcion == '2':
            manejar_listado_libros(db)
        elif opcion == '3':
            manejar_buscar_libros(db)
        elif opcion == '4':
            manejar_actualizar_libro(db)
        elif opcion == '5':
            manejar_eliminar_libro(db)
        elif opcion == '6':
            print("\n ¡Gracias por usar el Administrador de Biblioteca! Saliendo...")
            break
        else:
            print("\n Opción no válida. Por favor, ingrese un número del 1 al 6.")

if __name__ == "__main__":
    main()
