# Sistema de control de acceso con reconocimiento facial

Sistema de seguridad que usa una cámara para reconocer el rostro de una persona y, si está autorizada, activa una etapa de potencia (a través de un Arduino) para dar acceso a un sistema. Cada acceso reconocido se guarda en una base de datos MySQL.

Corre en una **Raspberry Pi** con Python y OpenCV. El Arduino se encarga solo de la parte de potencia.

---

## 1. Cómo funciona

```
 ┌────────┐  video  ┌──────────────────────────┐  serial USB   ┌─────────┐   ┌──────────────┐
 │ Cámara │ ──────► │ Raspberry Pi (final.py)  │ ────────────► │ Arduino │──►│ Etapa de     │
 └────────┘         │  1. Detecta rostro       │ "activar" /   └─────────┘   │ potencia     │
                    │  2. Lo compara (LBPH)    │ "desactivar"                └──────────────┘
                    │  3. Decide               │
                    └───────────┬──────────────┘
                                │ INSERT
                                ▼
                         ┌─────────────┐
                         │ MySQL       │  bd_segurity.accesos
                         └─────────────┘
```

**Ciclo de `final.py`:**

1. Toma un frame de la cámara y lo pasa a escala de grises.
2. Detecta rostros con un clasificador Haar Cascade (`haarcascade_frontalface_default.xml`, incluido en OpenCV).
3. Recorta el rostro y lo redimensiona a 150x150.
4. Lo compara contra el modelo entrenado (`modeloLBPHFace.xml`) con el reconocedor **LBPH**, que devuelve `(etiqueta, distancia)`.
5. Si la distancia es **menor a 70**, la persona queda reconocida:
   - envía `activar` al Arduino,
   - guarda el nombre y la hora en la tabla `accesos`.
6. Si no, muestra "Desconocido" y envía `desactivar`.
7. Se cierra presionando **ESC**.

El nombre mostrado sale de la lista de carpetas dentro de `Data/` (`imagePaths[etiqueta]`).

---

## 2. Estructura del repositorio

```
Reconocimiento/
├── README.md                  Este archivo
├── requirements.txt           Dependencias de Python
├── .gitignore                 Excluye Data/, venv/, caché
├── esquema.sql                Crea la base de datos y la tabla accesos
│
├── final.py                   ★ Programa final (Raspberry): reconocimiento + MySQL + Arduino
│
├── capturandoRostros.py       Paso 1: captura fotos de una persona con la cámara
├── entrenandoRF.py            Paso 2: entrena el modelo a partir de Data/
├── ReconocimientoFacial.py    Paso 3 (prueba): reconocimiento solo con cámara, sin base de datos
├── ReconocimientoConSQL.py    Prueba intermedia: reconocimiento + MySQL (sin Arduino)
├── modeloLBPHFace.xml         Modelo entrenado (generado por entrenandoRF.py)
│
└── pruebas/
    └── sql.py                 Prueba suelta de conexión MySQL (no forma parte del sistema)

Data/                          (NO está en el repo) Fotos de rostros, una carpeta por persona
└── <nombre>/rotro_0.jpg ... rotro_299.jpg
```

| Archivo | Qué hace | Dónde se usa |
|---|---|---|
| `capturandoRostros.py` | Guarda 300 rostros (150x150) en `Data/<personName>/`. Cambiar la variable `personName` antes de ejecutar. | PC o Raspberry |
| `entrenandoRF.py` | Lee todas las carpetas de `Data/`, entrena LBPH y escribe `modeloLBPHFace.xml`. | PC o Raspberry |
| `ReconocimientoFacial.py` | Muestra en pantalla quién es cada rostro. Útil para ajustar el umbral. | PC (Windows) |
| `ReconocimientoConSQL.py` | Igual que el anterior, pero registra accesos en MySQL. | PC (Windows) |
| `final.py` | Sistema completo en producción. | Raspberry Pi |

---

## 3. Qué necesita para funcionar

### Hardware
- Raspberry Pi (con Raspberry Pi OS) y pantalla/monitor (el script usa `cv2.imshow`).
- Cámara USB (o la cámara de la Raspberry, vista como `/dev/video0`).
- Arduino conectado por USB a la Raspberry (aparece como `/dev/ttyACM0`).
- Etapa de potencia controlada por el Arduino (relé, optoacoplador, etc.).

### Software
- Python 3
- Paquetes de `requirements.txt`:
  - `opencv-contrib-python` — **debe ser la versión *contrib***, porque `cv2.face` no viene en `opencv-python`.
  - `numpy`, `pyserial`, `mysql-connector-python`, `imutils`
- Servidor **MySQL / MariaDB**.

### Base de datos
Configuración que usa `final.py` (está escrita directamente en el código):

| Dato | Valor |
|---|---|
| Host | `localhost` |
| Usuario | `root` |
| Contraseña | `12345678` |
| Base de datos | `bd_segurity` |
| Tabla | `accesos (usuario, entrada)` |

El esquema no estaba en el proyecto; este es el que el código necesita (inferido de la consulta `INSERT`):

```sql
CREATE DATABASE IF NOT EXISTS bd_segurity;
USE bd_segurity;
CREATE TABLE IF NOT EXISTS accesos (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL,
    entrada DATETIME    NOT NULL
);
```

### Arduino
El sketch **no se conserva en este repositorio**. Debe cumplir este protocolo:

- Puerto serial a **9600 baudios**.
- Recibe texto ASCII, **sin salto de línea al final**:
  - `activar` → activa la etapa de potencia.
  - `desactivar` → la desactiva.

### Archivos y rutas
- `modeloLBPHFace.xml` debe estar en la carpeta desde donde se ejecuta el script (la ruta es relativa).
- Carpeta `Data/` con una subcarpeta por persona. Rutas configuradas en el código:
  - `final.py` → `/home/pi/Desktop/Reconocimiento/Data`
  - Resto de scripts → `E:\Reconocimiento\Data` (Windows; cambiar según tu equipo)

---

## 4. Instalación en la Raspberry Pi

```bash
# Dependencias del sistema
sudo apt update
sudo apt install -y python3-venv python3-pip mariadb-server libatlas-base-dev

# Permiso para usar el puerto serial del Arduino
sudo usermod -a -G dialout $USER      # luego cerrar sesión y volver a entrar

# Proyecto y entorno virtual
git clone <URL-del-repositorio> /home/pi/Desktop/Reconocimiento
cd /home/pi/Desktop/Reconocimiento
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Base de datos (ver sección 3 para el SQL)
sudo mysql < esquema.sql
```

## 5. Uso

**Registrar una persona nueva y reentrenar:**

```bash
# 1. Editar personName en capturandoRostros.py y ejecutar (ESC para terminar antes)
python3 capturandoRostros.py

# 2. Reentrenar el modelo con TODAS las personas de Data/
python3 entrenandoRF.py
```

**Ejecutar el sistema:**

```bash
python3 final.py
```

---

## 6. Notas importantes

- **El orden de `Data/` importa.** El nombre que se muestra sale de `os.listdir(Data)[etiqueta]`. Si se agregan, borran o renombran carpetas, hay que **reentrenar el modelo en la misma máquina** donde se va a ejecutar; de lo contrario el nombre mostrado puede ser incorrecto.
- El modelo incluido en este repo tiene **301 rostros y una sola etiqueta (`1`)**: se entrenó con una sola persona, y `Data/` tenía otra carpeta antes en la lista.
- El umbral de reconocimiento es `70` (LBPH): cuanto **menor** la distancia, mayor la coincidencia.
- La carpeta `Data/` está en `.gitignore` a propósito: son fotos de rostros (datos biométricos). No incluir `.gitkeep` dentro de `Data/`, porque el código lo contaría como una persona.

## 7. Pendientes conocidos

Problemas identificados que se resolverán más adelante:

- [ ] Credenciales de MySQL escritas en el código (mover a variables de entorno o archivo de configuración).
- [ ] Rutas fijas (`E:\...` y `/home/pi/...`) → hacerlas configurables.
- [ ] Se inserta un registro en la base de datos en cada frame mientras haya un rostro reconocido.
- [ ] Sin detección de "persona real": una foto o video podría engañar al sistema.
- [ ] Consultas SQL armadas con `.format()` → usar consultas parametrizadas.
- [ ] Falta el sketch del Arduino y el script SQL del esquema.
