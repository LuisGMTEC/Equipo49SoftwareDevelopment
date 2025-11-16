import json

import requests

BASE_URL = "http://127.0.0.1:8000"


def create_user(userName: str, userEmail: str):
    url = f"{BASE_URL}/users/"
    payload = {"userName": userName, "userEmail": userEmail}
    # LLAMADA A LA FAST API APP
    response = requests.post(url, json=payload)

    if response.status_code == 201:
        print("✅ Usuario creado correctamente")
    else:
        print("❌ Error creando usuario:", response.text)
    return response.json()["userId"]


def get_user(user_id: str):
    url = f"{BASE_URL}/users/{user_id}"
    # LLAMADA A LA FAST API APP
    response = requests.get(url)

    if response.status_code == 200:
        print("✅ Usuario encontrado:")
    else:
        print("❌ Error obteniendo usuario:", response.text)
    return response.json()


def get_all_users():
    url = f"{BASE_URL}/users/"
    # LLAMADA A LA FAST API APP
    response = requests.get(url)

    if response.status_code == 200:
        print("✅ Lista de usuarios:")
    else:
        print("❌ Error obteniendo usuarios:", response.text)
    return response.json()


def update_user(user_id: str, userName: str, userEmail: str):
    url = f"{BASE_URL}/users/{user_id}"
    payload = {}

    if not all([userName, userEmail]):
        raise ValueError("Se debe proporcionar al menos un campo para actualizar.")

    if userName:
        payload["userName"] = userName

    if userEmail:
        payload["userEmail"] = userEmail

    # LLAMADA A LA FAST API APP
    response = requests.put(url, json=payload)

    if response.status_code == 200:
        print("✅ Usuario actualizado correctamente")
    else:
        print("❌ Error actualizando usuario:", response.text)
    return response.json()


def delete_user(user_id: str):
    url = f"{BASE_URL}/users/{user_id}"
    # LLAMADA A LA FAST API APP
    response = requests.delete(url)

    if response.status_code in (200, 204):
        print("✅ Usuario eliminado correctamente")
    else:
        print("❌ Error eliminando usuario:", response.text)


if __name__ == "__main__":
    # ----- DEMO -----

    # 1. Crear usuario
    new_user_id = create_user("Luis Ángel", "luis@example.com")
    print("Nuevo ID de usuario:", new_user_id)

    # 2. Leer usuario individual
    user_data = get_user(new_user_id)
    print("Datos del usuario:\n", json.dumps(user_data, indent=4, ensure_ascii=False))

    # 3. Leer lista de usuarios
    all_users_data = get_all_users()
    print(
        "Lista de usuarios:\n", json.dumps(all_users_data, indent=4, ensure_ascii=False)
    )

    # 4. Actualizar usuario
    updated_user_data = update_user(
        new_user_id, userName="Luis Ángel Updated", userEmail="luis.updated@example.com"
    )
    print(
        "Datos del usuario actualizado:\n",
        json.dumps(updated_user_data, indent=4, ensure_ascii=False),
    )

    # 5. Eliminar usuario
    delete_user(new_user_id)
