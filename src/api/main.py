import os
from typing import Optional
import logging
import sys
import firebase_admin
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, firestore
from pydantic import BaseModel, Field
from src.api.rag_service import rag_answer, rag_answer_using_vector_store

# Cargar .env
load_dotenv(find_dotenv())

logger = None

def get_logger(logger_name="assistant", level="INFO"):

    global logger

    if logger is None:
        logger = logging.getLogger(logger_name)
        formatter = logging.Formatter(
            "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
        )
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)
        #fhdlr = logging.FileHandler("myapp.log")
        logger.addHandler(handler)
        #logger.addHandler(fhdlr)
        logger.setLevel(level)
        
    return logger

logger = get_logger()

# --- 1. Inicialización de Firebase ---
# Inicializar Firebase Admin SDK
if not firebase_admin._apps:
    # Opción 1: Usar archivo de credenciales
    # cred = credentials.Certificate("path/to/serviceAccountKey.json")

    # Opción 2: Usar credenciales por defecto (recomendado para producción)
    cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred)

# Obtener referencia a Firestore
db = firestore.client()
users_collection = db.collection("users")


# --- 2. Modelos de Datos (Pydantic) ---
class UserCreate(BaseModel):
    """Modelo para crear un nuevo usuario (payload de POST)."""

    userName: str = Field(...)
    userEmail: str = Field(...)


class UserInDB(UserCreate):
    """Modelo completo del usuario, tal como se almacena."""

    userId: str = Field(...)


class UserUpdate(BaseModel):
    """Modelo para actualizar un usuario (payload de PUT/PATCH)."""

    userName: Optional[str] = Field(default=None)
    userEmail: Optional[str] = Field(default=None)

class RAGRequest(BaseModel):
    question: str = Field(...)


class RAGResponse(BaseModel):
    answer: str = Field(...)

# --- 3. Inicialización de la Aplicación FastAPI ---
app = FastAPI(
    title="User CRUD API with Firebase",
    description="Implementación de operaciones CRUD para la colección 'users' en Firebase Firestore.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. Funciones CRUD y Endpoints ---


# 4.1. GET - Obtener un usuario por ID
@app.get("/users/{user_id}", response_model=UserInDB, tags=["Users"])
def read_user(user_id: str):
    """
    Obtiene los detalles de un usuario específico usando su ID de Firestore.
    """
    try:
        doc_ref = users_collection.document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=404, detail=f"User with ID '{user_id}' not found"
            )

        user_data = doc.to_dict()
        user_data["userId"] = doc.id

        return UserInDB(**user_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")


# 4.2. GET - Obtener la lista de todos los usuarios
@app.get("/users/", response_model=list[UserInDB], tags=["Users"])
def read_users():
    """
    Devuelve la lista completa de todos los usuarios registrados en Firestore.
    """
    try:
        docs = users_collection.stream()
        users = []

        for doc in docs:
            user_data = doc.to_dict()
            user_data["userId"] = doc.id
            users.append(UserInDB(**user_data))

        return users

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")


# 4.3. POST - Crear un nuevo usuario
@app.post("/users/", response_model=UserInDB, status_code=201, tags=["Users"])
def create_user(user: UserCreate):
    """
    Crea un nuevo usuario en Firestore.
    Firestore genera automáticamente un ID único para el documento.
    """
    try:
        # Convertir el modelo a diccionario
        user_data = user.model_dump()

        # Añadir el documento a Firestore (auto-genera ID)
        doc_ref = users_collection.add(user_data)

        # Obtener el ID generado
        new_id = doc_ref[1].id

        # Retornar el usuario creado con su ID
        return UserInDB(userId=new_id, userName=user.userName, userEmail=user.userEmail)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


# 4.4. PUT - Actualizar un usuario existente
@app.put("/users/{user_id}", response_model=UserInDB, tags=["Users"])
def update_user(user_id: str, user_update: UserUpdate):
    """
    Actualiza un usuario existente en Firestore usando su ID.
    """
    try:
        logger.info(f"Updating user with ID: {user_id} with data: {user_update}")
        doc_ref = users_collection.document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=404, detail=f"User with ID '{user_id}' not found"
            )

        # Obtener datos actuales
        current_data = doc.to_dict()

        # Obtener solo los campos que se van a actualizar
        update_data = user_update.model_dump(exclude_unset=True)

        if not update_data:
            # Si no hay datos para actualizar, retornar el usuario actual
            current_data["userId"] = doc.id
            return UserInDB(**current_data)

        # Actualizar el documento en Firestore
        doc_ref.update(update_data)

        # Obtener el documento actualizado
        updated_doc = doc_ref.get()
        updated_data = updated_doc.to_dict()
        logger.info(f"Updated user data: {updated_data}")
        updated_data["userId"] = updated_doc.id

        return UserInDB(**updated_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


# 4.5. DELETE - Eliminar un usuario
@app.delete("/users/{user_id}", status_code=204, tags=["Users"])
def delete_user(user_id: str):
    """
    Elimina un usuario de Firestore usando su ID.
    """
    try:
        doc_ref = users_collection.document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=404, detail=f"User with ID '{user_id}' not found"
            )

        # Eliminar el documento
        doc_ref.delete()

        return

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


# 5. GET - Endpoint raíz con mensaje de bienvenida
@app.get("/", tags=["Users"])
def welcome_message():
    """
    Mensaje de bienvenida en el endpoint raíz.
    """
    return {"message": "Welcome to the User CRUD API with Firebase!"}

@app.post("/rag/ask", response_model=RAGResponse, tags=["RAG"])
def ask_rag(request: RAGRequest):
    """
    RAG endpoint: searches FAQ knowledge in Firestore and uses Gemini to produce a final answer.
    """
    try:
        answer = rag_answer(request.question)
        return RAGResponse(answer=answer)

    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")


@app.post("/rag/generate_answer", tags=["RAG"])
def generate_answer(request: RAGRequest):
    try:
        answer = rag_answer_using_vector_store(request.question)
        return {"llm_generated_answer": answer}

    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")