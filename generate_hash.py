import getpass

import bcrypt


def generate_hash() -> None:
    """
    Genera un hash seguro para una contraseña usando bcrypt.
    """
    try:
        # Usar getpass para que la contraseña no se muestre en la terminal
        password = getpass.getpass("Introduce la contraseña maestra que deseas usar: ")
        if not password:
            print("Error: La contraseña no puede estar vacía.")
            return

        # Generar el hash
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        print("\n¡Hash generado con éxito!")
        print(
            "Copia la siguiente línea completa y pégala en tu archivo .env "
            "como el valor de MASTER_PASSWORD_HASH:\n"
        )
        print(f"{hashed_password.decode('utf-8')}")

    except Exception as e:
        print(f"\nOcurrió un error al generar el hash: {e}")

if __name__ == "__main__":
    generate_hash()
