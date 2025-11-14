import click
from flask import current_app
# Importamos db desde nuestro archivo local de extensiones
from .extensions import db
# 1. CORRECCIÓN: Importar Role desde el módulo de autenticación
from .auth.models import Role 

def register_commands(app):
    """Registra todos los comandos personalizados de la CLI en la aplicación Flask."""
    
    # ----------------------------------------------------
    # Comando CLI para crear roles base
    # ----------------------------------------------------
    @app.cli.command("create-roles")
    def create_roles_command():
        """Crea los roles base: ADMIN (3), EDITOR (2), READER (1) si no existen.
        Esto asegura que el rol por defecto (ID 1 en User) sea 'READER'.
        """
        
        app = current_app 
        
        with app.app_context():
            print("--- Iniciando verificación y creación de roles ---")
            
            # Definimos los roles y sus IDs deseadas: (ID, Nombre)
            roles_to_create = [
                (1, "READER"), 
                (2, "EDITOR"), 
                (3, "ADMIN")
            ]
            
            # Recorrer la lista de roles
            for role_id, role_name in roles_to_create:
                # 1. Verificar si el rol ya existe por NOMBRE (ya que el nombre es UNIQUE)
                # Usamos la sintaxis moderna de SQLAlchemy
                role_obj = db.session.execute(db.select(Role).filter_by(name=role_name)).scalar_one_or_none()
                
                if role_obj is None:
                    # 2. Si no existe, crearlo. Intentamos establecer el ID manualmente.
                    # Esto solo funcionará si la tabla de roles está vacía o si el ID no ha sido usado.
                    new_role = Role(id=role_id, name=role_name)
                    db.session.add(new_role)
                    print(f"-> Rol '{role_name}' (ID deseado: {role_id}) agregado para commit.")
                else:
                    # Si ya existe, confirmamos el ID.
                    print(f"-> Rol '{role_name}' ya existe (ID: {role_obj.id}). Omitiendo.")
            
            try:
                db.session.commit()
                print("--- Roles base creados/verificados con éxito. ---")
            except Exception as e:
                db.session.rollback()
                # Notificamos si hay un error de commit (típicamente por conflicto de Primary Key/ID)
                print(f"!!! Error al commitear los roles (ej. conflicto de ID): {e}")
                print("Asegúrate de que la tabla 'roles' esté vacía si quieres garantizar los IDs 1, 2, 3.")

            print("\nPara ejecutar este comando, usa: flask create-roles")