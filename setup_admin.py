import bcrypt, pymysql
from pymysql.cursors import DictCursor

DB = {"host":"localhost","port":3306,"user":"root","password":"","database":"gympro","charset":"utf8mb4","cursorclass":DictCursor}

def main():
    ah = bcrypt.hashpw(b"Admin1234!", bcrypt.gensalt()).decode()
    mh = bcrypt.hashpw(b"Miembro123!", bcrypt.gensalt()).decode()
    eh = bcrypt.hashpw(b"Entrena123!", bcrypt.gensalt()).decode()
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET password_hash=%s WHERE email='admin@gympro.com'",(ah,))
            cur.execute("UPDATE usuarios SET password_hash=%s WHERE rol_id=3",(mh,))
            cur.execute("UPDATE entrenadores SET password_hash=%s",(eh,))
        conn.commit()
        print("[OK] Contraseñas actualizadas.")
        print("     Admin      -> admin@gympro.com / Admin1234!")
        print("     Miembros   -> cualquier email / Miembro123!")
        print("     Entrenadores -> cualquier email entrenador / Entrena123!")
        print("\nEntrenadores de ejemplo:")
        emails = ["carlos.e@gympro.com","laura.e@gympro.com","roberto.e@gympro.com","vale.e@gympro.com","andres.e@gympro.com"]
        for e in emails:
            print(f"    {e} / Entrena123!")
    finally:
        conn.close()

if __name__=="__main__":
    main()
