#  Proyecto: Administrador de Biblioteca (MariaDB + SQLAlchemy ORM)

## Descripción del Proyecto
Este proyecto es una migración de la aplicación CLI de gestión de biblioteca. Sustituye la base de datos SQLite por **MariaDB** (o MySQL) y emplea **SQLAlchemy** como Object-Relational Mapper (ORM) para manejar las operaciones CRUD de manera orientada a objetos.

##  Requisitos y Configuración del Entorno

### 1. Instalación de MariaDB/MySQL
Debe tener un servidor MariaDB o MySQL instalado y en ejecución en su máquina local (`localhost`).

* **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt update
    sudo apt install mariadb-server
    sudo systemctl start mariadb
    ```
* **macOS (Homebrew):**
    ```bash
    brew install mariadb
    brew services start mariadb
    ```
* **Windows:**
    Descargue el instalador de MariaDB o MySQL Community Server y siga los pasos de instalación.

### 2. Configuración de la Base de Datos

Debe crear la base de datos y un usuario para la aplicación (usando las credenciales definidas en el archivo `.env`).

Conéctese a su servidor MariaDB/MySQL como root (o un usuario con privilegios) y ejecute los siguientes comandos SQL:

```sql
-- Crear la base de datos
CREATE DATABASE biblioteca_sqlalchemy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear el usuario de la aplicación (ajuste la contraseña)
CREATE USER 'biblioteca_user'@'localhost' IDENTIFIED BY 'una_clave_segura';

-- Asignar permisos al usuario sobre la base de datos
GRANT ALL PRIVILEGES ON biblioteca_sqlalchemy.* TO 'biblioteca_user'@'localhost';

FLUSH PRIVILEGES;
