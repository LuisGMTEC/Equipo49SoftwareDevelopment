# Equipo49SoftwareDevelopment
Este es el repositorio del equipo 49 para la materia "Análisis, Diseño y Construcción de Software" del  trimestre sep-dic de 2025 en la Maestría en Inteligencia Artificial Aplicada del Instituto Tecnológico y de Estudios Superiores de Monterrey

# Empezando

Este proyecto combina un **frontend en HTML/CSS/JS** y un **backend con FastAPI** para ofrecer:
- Un **Chatbot FAQ** conectado a Firebase (Firestore)
- Un **CRUD completo sobre la colección de usuarios** consumiendo una API de FastAPI

## 🧩 Objetivo

Levantar el proyecto en **3 sencillos pasos**:

1. Clonar la rama `dev`
2. Configurar el archivo `.env` con las credenciales de Firebase
3. Levantar la API (FastAPI) y el frontend

---

## 🗂️ Estructura del proyecto

├── .env
├── requirements.txt
├── api
│    └── main.py
│ 
│
└── frontend  
    ├── index.html  
    ├── app.js  
    └── styles.css  

## ⚙️ Paso 1. Clonar la rama `dev`

Clona el repositorio y entra al proyecto:

```bash
git clone -b dev <URL_DEL_REPO>
cd <nombre_del_proyecto>
```

## Paso 2. Obtener y configurar credenciales Firebase

1. Consigue tu archivo MyFirebaseServiceAccountKey.json desde tu consola de Firebase.

2. Guárdalo en una ubicación segura de tu equipo.

3. En el archivo .env del proyecto, define la variable:

```txt
GOOGLE_APPLICATION_CREDENTIALS=<RUTA_ABSOLUTA_HACIA_MyFirebaseServiceAccountKey.json>
```

⚠️ Importante: Usa ruta absoluta, no relativa.

## Paso 3. Crear entorno virtual e instalar dependencias

Desde la raíz del proyecto:

* Crear entorno virtual

```bash
python -m venv .venv
```
* Activar entorno (Windows)

```powershell
.venv\Scripts\activate
```

* Activar entorno (Linux/Mac)
```bash
source .venv/bin/activate
```

* Instalar dependencias

```bash
pip install -r requirements.txt
```

## Paso 4. Levantar los servicios

### 1. Backend (FastAPI)

* Desde la raíz del proyecto, ejecuta:

```bash
uvicorn src.api.main:app --reload
```

### 2. Frontend (HTML/JS)

* Cambiar directorio a la carpeta frontend

```bash
cd frontend
```

* Ejecutar el frontend usando python

```bash
python -m http.server
```

* Visitar: http://127.0.0.1:8000



