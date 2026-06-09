from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
BOGOTA = ZoneInfo("America/Bogota")
def bogota_now(): return datetime.now(BOGOTA)
def bogota_date(): return bogota_now().date()
def bogota_time(): return bogota_now().strftime("%H:%M:%S")
import bcrypt, os, uuid
from werkzeug.utils import secure_filename
from config import get_connection, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'valoraciones')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(f): return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# ─── DECORADORES ───────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json: return jsonify({"error":"No autorizado"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("rol") not in roles:
                if request.is_json: return jsonify({"error":"Permisos insuficientes"}), 403
                return redirect(url_for("inicio"))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─── PÁGINAS ───────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session: return redirect(url_for("inicio"))
    return redirect(url_for("login_page"))

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/inicio")
@login_required
def inicio():
    rol = session.get("rol")
    if rol == "miembro":     return render_template("inicio_miembro.html")
    if rol == "entrenador":  return render_template("inicio_entrenador.html")
    return render_template("inicio_admin.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("inicio"))

@app.route("/usuarios")
@login_required
@role_required("administrador")
def usuarios_page():
    return render_template("usuarios.html")

@app.route("/entrenadores")
@login_required
@role_required("administrador","entrenador")
def entrenadores_page():
    return render_template("entrenadores.html")

@app.route("/rutinas")
@login_required
def rutinas_page():
    if session.get("rol") == "miembro":
        return render_template("rutinas_miembro.html")
    return render_template("rutinas.html")

@app.route("/asistencia")
@login_required
@role_required("administrador","entrenador")
def asistencia_page():
    return render_template("asistencia.html")

@app.route("/horarios")
@login_required
def horarios_page():
    return render_template("horarios.html")

@app.route("/reportes")
@login_required
@role_required("administrador","entrenador")
def reportes_page():
    return render_template("reportes.html")

@app.route("/membresias")
@login_required
@role_required("administrador")
def membresias_page():
    return render_template("membresias.html")

@app.route("/perfil")
@login_required
def perfil_page():
    return render_template("perfil.html")

@app.route("/dieta")
@login_required
def dieta_page():
    return render_template("dieta.html")

@app.route("/valoracion/<int:uid>")
@login_required
@role_required("administrador","entrenador")
def valoracion_page(uid):
    return render_template("valoracion.html", uid=uid)

# ─── AUTH ──────────────────────────────────────────────────

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email","").strip()
    password = data.get("password","")
    if not email or not password:
        return jsonify({"error":"Email y contraseña requeridos"}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Buscar en usuarios
            cur.execute("SELECT u.*,r.nombre AS rol FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.email=%s",(email,))
            user = cur.fetchone()
            if user and user["estado"]=="activo" and bcrypt.checkpw(password.encode(),user["password_hash"].encode()):
                session.update({"user_id":user["id"],"nombre":f"{user['nombre']} {user['apellido']}","email":user["email"],"rol":user["rol"],"tipo":"usuario"})
                return jsonify({"message":"ok","rol":user["rol"]}), 200
            # Buscar en entrenadores
            cur.execute("SELECT * FROM entrenadores WHERE email=%s AND estado='activo'",(email,))
            ent = cur.fetchone()
            if ent and ent.get("password_hash") and bcrypt.checkpw(password.encode(),ent["password_hash"].encode()):
                session.update({"user_id":ent["id"],"nombre":f"{ent['nombre']} {ent['apellido']}","email":ent["email"],"rol":"entrenador","tipo":"entrenador"})
                return jsonify({"message":"ok","rol":"entrenador"}), 200
        return jsonify({"error":"Credenciales incorrectas"}), 401
    finally:
        conn.close()

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message":"ok"}), 200

# ─── USUARIOS ──────────────────────────────────────────────

@app.route("/api/usuarios", methods=["GET"])
@login_required
@role_required("administrador","entrenador")
def get_usuarios():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id,u.cedula,u.nombre,u.apellido,u.email,u.telefono,u.genero,
                CAST(u.fecha_nacimiento AS CHAR) AS fecha_nacimiento,
                CAST(u.fecha_registro AS CHAR) AS fecha_registro,
                u.estado,r.nombre AS rol,
                (SELECT COUNT(*) FROM valoraciones_fisicas v WHERE v.usuario_id=u.id AND v.completada=1) AS tiene_valoracion
                FROM usuarios u JOIN roles r ON r.id=u.rol_id ORDER BY u.id
            """)
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/usuarios/<int:uid>", methods=["GET"])
@login_required
def get_usuario(uid):
    if session.get("rol") not in ["administrador","entrenador"] and session.get("user_id") != uid:
        return jsonify({"error":"Permisos insuficientes"}), 403
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id,u.cedula,u.nombre,u.apellido,u.email,u.telefono,u.genero,
                CAST(u.fecha_nacimiento AS CHAR) AS fecha_nacimiento,
                CAST(u.fecha_registro AS CHAR) AS fecha_registro,u.estado,r.nombre AS rol
                FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.id=%s
            """,(uid,))
            return jsonify(cur.fetchone()), 200
    finally:
        conn.close()

@app.route("/api/usuarios/check-cedula", methods=["POST"])
def check_cedula():
    data = request.get_json()
    cedula = data.get("cedula","").strip()
    uid = data.get("usuario_id")
    if not cedula: return jsonify({"exists":False}), 200
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if uid:
                cur.execute("SELECT id FROM usuarios WHERE cedula=%s AND id!=%s",(cedula,uid))
            else:
                cur.execute("SELECT id FROM usuarios WHERE cedula=%s",(cedula,))
            return jsonify({"exists": cur.fetchone() is not None}), 200
    finally:
        conn.close()

@app.route("/api/usuarios", methods=["POST"])
@login_required
@role_required("administrador")
def create_usuario():
    data = request.get_json()
    required = ["cedula","nombre","apellido","email","password","rol_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error":f"Campos obligatorios faltantes: {', '.join(missing)}"}), 400
    if len(data["password"]) < 6:
        return jsonify({"error":"La contraseña debe tener mínimo 6 caracteres"}), 400
    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verificar cédula
            cur.execute("SELECT id FROM usuarios WHERE cedula=%s",(data["cedula"],))
            if cur.fetchone():
                return jsonify({"error":f"Ya existe un usuario registrado con la cédula {data['cedula']}"}), 400
            cur.execute("SELECT id FROM usuarios WHERE email=%s",(data["email"],))
            if cur.fetchone():
                return jsonify({"error":"Ya existe un usuario con ese email"}), 400
            cur.execute(
                "INSERT INTO usuarios(cedula,nombre,apellido,email,password_hash,telefono,fecha_nacimiento,genero,rol_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (data["cedula"],data["nombre"],data["apellido"],data["email"],hashed,
                 data.get("telefono"),data.get("fecha_nacimiento") or None,data.get("genero"),data["rol_id"])
            )
            uid = cur.lastrowid
            # Membresía
            mb = data.get("membresia",{})
            if mb and mb.get("tipo_id") and mb.get("monto_pagado"):
                cur.execute("SELECT duracion_dias FROM tipos_membresia WHERE id=%s",(mb["tipo_id"],))
                tipo = cur.fetchone()
                if tipo:
                    cur.execute(
                        "INSERT INTO membresias(usuario_id,tipo_id,monto_pagado,fecha_fin) VALUES(%s,%s,%s,DATE_ADD(CURRENT_DATE,INTERVAL %s DAY))",
                        (uid,mb["tipo_id"],mb["monto_pagado"],tipo["duracion_dias"])
                    )
        conn.commit()
        return jsonify({"message":"Usuario creado","id":uid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/usuarios/<int:uid>", methods=["PUT"])
@login_required
@role_required("administrador")
def update_usuario(uid):
    data = request.get_json()
    if not all([data.get("cedula"),data.get("nombre"),data.get("apellido"),data.get("email")]):
        return jsonify({"error":"Cédula, nombre, apellido y email son obligatorios"}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE cedula=%s AND id!=%s",(data["cedula"],uid))
            if cur.fetchone():
                return jsonify({"error":f"Ya existe otro usuario con la cédula {data['cedula']}"}), 400
            cur.execute(
                "UPDATE usuarios SET cedula=%s,nombre=%s,apellido=%s,email=%s,telefono=%s,fecha_nacimiento=%s,genero=%s,estado=%s WHERE id=%s",
                (data["cedula"],data["nombre"],data["apellido"],data["email"],data.get("telefono"),
                 data.get("fecha_nacimiento") or None,data.get("genero"),data.get("estado","activo"),uid)
            )
            if data.get("password"):
                hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
                cur.execute("UPDATE usuarios SET password_hash=%s WHERE id=%s",(hashed,uid))
        conn.commit()
        return jsonify({"message":"Actualizado"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/usuarios/<int:uid>", methods=["DELETE"])
@login_required
@role_required("administrador")
def delete_usuario(uid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET estado='inactivo' WHERE id=%s",(uid,))
            cur.execute("INSERT INTO auditoria_log(tabla,operacion,registro_id,detalle,usuario_id) VALUES('usuarios','DELETE',%s,'Usuario desactivado',%s)",(uid,session["user_id"]))
        conn.commit()
        return jsonify({"message":"Desactivado"}), 200
    finally:
        conn.close()

@app.route("/api/usuarios/<int:uid>/activar", methods=["PUT"])
@login_required
@role_required("administrador")
def activar_usuario(uid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET estado='activo' WHERE id=%s",(uid,))
        conn.commit()
        return jsonify({"message":"Activado"}), 200
    finally:
        conn.close()

# ─── VALORACIÓN FÍSICA ─────────────────────────────────────

@app.route("/api/valoracion/<int:uid>", methods=["GET"])
@login_required
def get_valoracion(uid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM valoraciones_fisicas WHERE usuario_id=%s ORDER BY fecha_registro DESC LIMIT 1",(uid,))
            val = cur.fetchone()
            if val:
                cur.execute("SELECT * FROM fotos_valoracion WHERE valoracion_id=%s",(val["id"],))
                val["fotos"] = cur.fetchall()
            return jsonify(val), 200
    finally:
        conn.close()

@app.route("/api/valoracion/<int:uid>", methods=["POST"])
@login_required
@role_required("administrador","entrenador")
def save_valoracion(uid):
    data = request.get_json()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM valoraciones_fisicas WHERE usuario_id=%s ORDER BY fecha_registro DESC LIMIT 1",(uid,))
            existing = cur.fetchone()

            # Calcular IMC si hay datos
            peso = float(data.get("peso_kg",0) or 0)
            est  = float(data.get("estatura_cm",0) or 0)
            imc  = round(peso/((est/100)**2),2) if peso and est else data.get("imc")

            campos = dict(
                evaluador_nombre=data.get("evaluador_nombre"),
                fecha_valoracion=data.get("fecha_valoracion") or str(date.today()),
                edad=data.get("edad") or None,
                genero=data.get("genero"),
                estatura_cm=data.get("estatura_cm") or None,
                peso_kg=data.get("peso_kg") or None,
                imc=imc,
                fc_reposo=data.get("fc_reposo") or None,
                presion_arterial=data.get("presion_arterial"),
                porcentaje_grasa=data.get("porcentaje_grasa") or None,
                masa_muscular_kg=data.get("masa_muscular_kg") or None,
                masa_grasa_kg=data.get("masa_grasa_kg") or None,
                grasa_visceral=data.get("grasa_visceral") or None,
                porcentaje_agua=data.get("porcentaje_agua") or None,
                tasa_metabolica_basal=data.get("tasa_metabolica_basal") or None,
                perimetro_cuello=data.get("perimetro_cuello") or None,
                perimetro_hombros=data.get("perimetro_hombros") or None,
                perimetro_pecho=data.get("perimetro_pecho") or None,
                perimetro_cintura=data.get("perimetro_cintura") or None,
                perimetro_cadera=data.get("perimetro_cadera") or None,
                perimetro_brazo_izq_rel=data.get("perimetro_brazo_izq_rel") or None,
                perimetro_brazo_izq_con=data.get("perimetro_brazo_izq_con") or None,
                perimetro_brazo_der_rel=data.get("perimetro_brazo_der_rel") or None,
                perimetro_brazo_der_con=data.get("perimetro_brazo_der_con") or None,
                perimetro_muslo_izq_alt=data.get("perimetro_muslo_izq_alt") or None,
                perimetro_muslo_izq_med=data.get("perimetro_muslo_izq_med") or None,
                perimetro_muslo_der_alt=data.get("perimetro_muslo_der_alt") or None,
                perimetro_muslo_der_med=data.get("perimetro_muslo_der_med") or None,
                perimetro_pantorrilla_izq=data.get("perimetro_pantorrilla_izq") or None,
                perimetro_pantorrilla_der=data.get("perimetro_pantorrilla_der") or None,
                enfermedades=data.get("enfermedades"),
                lesiones=data.get("lesiones"),
                medicamentos=data.get("medicamentos"),
                fumador=int(data.get("fumador",0)),
                objetivo=data.get("objetivo","mantener"),
                nivel_actividad=data.get("nivel_actividad","poco_activo"),
                observaciones=data.get("observaciones"),
            )

            if existing:
                sets = ",".join(f"{k}=%s" for k in campos)
                cur.execute(f"UPDATE valoraciones_fisicas SET {sets} WHERE usuario_id=%s", list(campos.values())+[uid])
                val_id = existing["id"]
            else:
                cols = ",".join(["usuario_id"]+list(campos.keys()))
                placeholders = ",".join(["%s"]*( len(campos)+1))
                cur.execute(f"INSERT INTO valoraciones_fisicas({cols}) VALUES({placeholders})", [uid]+list(campos.values()))
                val_id = cur.lastrowid

            # También actualizar fecha_nacimiento y genero en usuario
            if data.get("genero"):
                cur.execute("UPDATE usuarios SET genero=%s WHERE id=%s",(data["genero"],uid))

        conn.commit()
        return jsonify({"message":"Valoración guardada","id":val_id}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/valoracion/<int:uid>/foto", methods=["POST"])
@login_required
@role_required("administrador","entrenador")
def upload_foto(uid):
    if "foto" not in request.files:
        return jsonify({"error":"No se envió archivo"}), 400
    file = request.files["foto"]
    tipo = request.form.get("tipo","otro")
    if not allowed_file(file.filename):
        return jsonify({"error":"Formato no permitido. Usa JPG, PNG o WEBP"}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM valoraciones_fisicas WHERE usuario_id=%s ORDER BY id DESC LIMIT 1",(uid,))
            val = cur.fetchone()
            if not val:
                return jsonify({"error":"Primero guarda la valoración"}), 400
            ext = file.filename.rsplit(".",1)[1].lower()
            filename = f"{uid}_{tipo}_{uuid.uuid4().hex[:8]}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            cur.execute("INSERT INTO fotos_valoracion(valoracion_id,usuario_id,tipo,ruta_archivo) VALUES(%s,%s,%s,%s)",
                        (val["id"],uid,tipo,f"uploads/valoraciones/{filename}"))
        conn.commit()
        return jsonify({"message":"Foto subida","ruta":f"uploads/valoraciones/{filename}"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/valoracion/<int:uid>/foto/<int:fid>", methods=["DELETE"])
@login_required
@role_required("administrador","entrenador")
def delete_foto(uid, fid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT ruta_archivo FROM fotos_valoracion WHERE id=%s AND usuario_id=%s",(fid,uid))
            foto = cur.fetchone()
            if foto:
                ruta = os.path.join(app.static_folder, foto["ruta_archivo"])
                if os.path.exists(ruta): os.remove(ruta)
            cur.execute("DELETE FROM fotos_valoracion WHERE id=%s",(fid,))
        conn.commit()
        return jsonify({"message":"Eliminada"}), 200
    finally:
        conn.close()

# ─── ENTRENADORES ──────────────────────────────────────────

@app.route("/api/entrenadores", methods=["GET"])
@login_required
def get_entrenadores():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id,cedula,nombre,apellido,email,especialidad,telefono,titulo,es_profesional,anos_experiencia,certificaciones,estado,CAST(fecha_ingreso AS CHAR) AS fecha_ingreso FROM entrenadores ORDER BY id")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/entrenadores", methods=["POST"])
@login_required
@role_required("administrador")
def create_entrenador():
    data = request.get_json()
    if not all(data.get(k) for k in ["cedula","nombre","apellido","email"]):
        return jsonify({"error":"Cédula, nombre, apellido y email son obligatorios"}), 400
    hashed = bcrypt.hashpw(b"Entrena123!", bcrypt.gensalt()).decode()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM entrenadores WHERE cedula=%s",(data["cedula"],))
            if cur.fetchone(): return jsonify({"error":"Ya existe un entrenador con esa cédula"}), 400
            cur.execute(
                "INSERT INTO entrenadores(cedula,nombre,apellido,email,password_hash,especialidad,telefono,titulo,universidad,es_profesional,anos_experiencia,certificaciones) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (data["cedula"],data["nombre"],data["apellido"],data["email"],hashed,
                 data.get("especialidad"),data.get("telefono"),data.get("titulo"),
                 data.get("universidad"),int(data.get("es_profesional",0)),
                 data.get("anos_experiencia",0),data.get("certificaciones"))
            )
        conn.commit()
        return jsonify({"message":"Creado. Contraseña inicial: Entrena123!"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/entrenadores/<int:eid>", methods=["PUT"])
@login_required
@role_required("administrador")
def update_entrenador(eid):
    data = request.get_json()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE entrenadores SET cedula=%s,nombre=%s,apellido=%s,especialidad=%s,telefono=%s,titulo=%s,universidad=%s,es_profesional=%s,anos_experiencia=%s,certificaciones=%s,estado=%s WHERE id=%s",
                (data.get("cedula"),data.get("nombre"),data.get("apellido"),data.get("especialidad"),
                 data.get("telefono"),data.get("titulo"),data.get("universidad"),
                 int(data.get("es_profesional",0)),data.get("anos_experiencia",0),
                 data.get("certificaciones"),data.get("estado","activo"),eid)
            )
        conn.commit()
        return jsonify({"message":"Actualizado"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

# ─── RUTINAS ───────────────────────────────────────────────

@app.route("/api/rutinas", methods=["GET"])
@login_required
def get_rutinas():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT r.*,CONCAT(e.nombre,' ',e.apellido) AS entrenador_nombre FROM rutinas r JOIN entrenadores e ON e.id=r.entrenador_id ORDER BY r.id")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/rutinas/<int:rid>", methods=["GET"])
@login_required
def get_rutina(rid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT r.*,CONCAT(e.nombre,' ',e.apellido) AS entrenador_nombre FROM rutinas r JOIN entrenadores e ON e.id=r.entrenador_id WHERE r.id=%s",(rid,))
            r = cur.fetchone()
            if not r: return jsonify({"error":"No encontrada"}), 404
            cur.execute("SELECT * FROM ejercicios WHERE rutina_id=%s ORDER BY dia,id",(rid,))
            r["ejercicios"] = cur.fetchall()
        return jsonify(r), 200
    finally:
        conn.close()

@app.route("/api/rutinas", methods=["POST"])
@login_required
@role_required("administrador","entrenador")
def create_rutina():
    data = request.get_json()
    if not all(data.get(k) for k in ["nombre","entrenador_id"]):
        return jsonify({"error":"Nombre y entrenador obligatorios"}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO rutinas(nombre,descripcion,objetivo,duracion_semanas,nivel,dias_por_semana,entrenador_id) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (data["nombre"],data.get("descripcion"),data.get("objetivo","general"),data.get("duracion_semanas",4),data.get("nivel","principiante"),data.get("dias_por_semana",3),data["entrenador_id"])
            )
            rid = cur.lastrowid
            for ej in data.get("ejercicios",[]):
                cur.execute("INSERT INTO ejercicios(rutina_id,nombre,series,repeticiones,descanso_seg,dia,notas) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (rid,ej["nombre"],ej.get("series",3),ej.get("repeticiones","10"),ej.get("descanso_seg",60),ej.get("dia",1),ej.get("notas","")))
        conn.commit()
        return jsonify({"message":"Creada","id":rid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/rutinas/<int:rid>", methods=["PUT"])
@login_required
@role_required("administrador","entrenador")
def update_rutina(rid):
    data = request.get_json()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE rutinas SET nombre=%s,descripcion=%s,objetivo=%s,duracion_semanas=%s,nivel=%s,dias_por_semana=%s WHERE id=%s",
                (data.get("nombre"),data.get("descripcion"),data.get("objetivo"),data.get("duracion_semanas"),data.get("nivel"),data.get("dias_por_semana"),rid))
        conn.commit()
        return jsonify({"message":"Actualizada"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/ejercicios/<int:rid>", methods=["POST"])
@login_required
@role_required("administrador","entrenador")
def add_ejercicio(rid):
    data = request.get_json()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO ejercicios(rutina_id,nombre,series,repeticiones,descanso_seg,dia,notas) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (rid,data["nombre"],data.get("series",3),data.get("repeticiones","10"),data.get("descanso_seg",60),data.get("dia",1),data.get("notas","")))
        conn.commit()
        return jsonify({"message":"Agregado","id":cur.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/ejercicios/<int:eid>", methods=["DELETE"])
@login_required
@role_required("administrador","entrenador")
def delete_ejercicio(eid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ejercicios WHERE id=%s",(eid,))
        conn.commit()
        return jsonify({"message":"Eliminado"}), 200
    finally:
        conn.close()

# ─── ASIGNACIONES ──────────────────────────────────────────

@app.route("/api/asignaciones", methods=["GET"])
@login_required
def get_asignaciones():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM v_miembros_rutinas")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/asignaciones", methods=["POST"])
@login_required
@role_required("administrador","entrenador")
def create_asignacion():
    data = request.get_json()
    uid = data.get("usuario_id")
    # Verificar que tiene valoración completa
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT completada FROM valoraciones_fisicas WHERE usuario_id=%s ORDER BY id DESC LIMIT 1",(uid,))
            val = cur.fetchone()
            if not val or not val["completada"]:
                return jsonify({"error":"El usuario no tiene una valoración física completa. Realiza la valoración antes de asignar una rutina."}), 400
            cur.execute("UPDATE asignaciones SET estado='cancelada' WHERE usuario_id=%s AND estado='activa'",(uid,))
            cur.execute("INSERT INTO asignaciones(usuario_id,rutina_id,entrenador_id,observaciones) VALUES(%s,%s,%s,%s)",
                (uid,data["rutina_id"],data["entrenador_id"],data.get("observaciones")))
        conn.commit()
        return jsonify({"message":"Rutina asignada"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/asignaciones/<int:aid>", methods=["DELETE"])
@login_required
@role_required("administrador","entrenador")
def delete_asignacion(aid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE asignaciones SET estado='cancelada' WHERE id=%s",(aid,))
        conn.commit()
        return jsonify({"message":"Removida"}), 200
    finally:
        conn.close()

# ─── ASISTENCIA ────────────────────────────────────────────

@app.route("/api/asistencia", methods=["GET"])
@login_required
def get_asistencia():
    uid = request.args.get("usuario_id")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if uid:
                cur.execute("SELECT * FROM v_asistencia_detalle WHERE usuario_id=%s",(uid,))
            else:
                cur.execute("SELECT * FROM v_asistencia_detalle LIMIT 300")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/asistencia/semana", methods=["GET"])
@login_required
@role_required("administrador","entrenador")
def asistencia_semana():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM v_asistencia_semana")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/asistencia/hoy", methods=["GET"])
@login_required
def asistencia_hoy():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM v_asistencia_hoy")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/asistencia", methods=["POST"])
@login_required
def registrar_asistencia():
    data = request.get_json()
    usuario_id = data.get("usuario_id") or session["user_id"]
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO asistencias(usuario_id,fecha,hora,registrado_por,observacion) VALUES(%s,%s,%s,%s,%s)",
                (usuario_id,str(bogota_date()),bogota_time(),session["user_id"],data.get("observacion")))
        conn.commit()
        return jsonify({"message":"Registrada","id":cur.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        if "Duplicate" in str(e):
            return jsonify({"error":"Ya tiene asistencia registrada hoy"}), 400
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/asistencia/<int:uid>/dia/<int:dia>", methods=["POST"])
@login_required
@role_required("administrador","entrenador")
def toggle_asistencia_dia(uid, dia):
    """Toggle asistencia para un día específico de la semana actual."""

    hoy = bogota_date()
    lunes = hoy - timedelta(days=hoy.weekday())
    fecha_dia = lunes + timedelta(days=dia-1)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM asistencias WHERE usuario_id=%s AND fecha=%s",(uid,fecha_dia))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM asistencias WHERE id=%s",(existing["id"],))
                conn.commit()
                return jsonify({"message":"Asistencia removida","asistio":False,"fecha":str(fecha_dia)}), 200
            else:
                dia_real = fecha_dia.weekday() + 1  # 1=lunes, 7=domingo
                cur.execute("INSERT INTO asistencias(usuario_id,fecha,dia_semana,registrado_por) VALUES(%s,%s,%s,%s)",
                    (uid,fecha_dia,dia_real,session["user_id"]))
                conn.commit()
                return jsonify({"message":"Asistencia registrada","asistio":True,"id":cur.lastrowid,"fecha":str(fecha_dia)}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()


@app.route("/api/asistencia/<int:uid>/fecha/<string:fecha_str>", methods=["POST"])
@login_required
@role_required("administrador","entrenador")
def toggle_asistencia_fecha(uid, fecha_str):
    """Toggle asistencia para una fecha específica."""
    from datetime import date as date_type
    try:
        fecha_dia = date_type.fromisoformat(fecha_str)
    except ValueError:
        return jsonify({"error":"Fecha inválida"}), 400
    dia_real = fecha_dia.weekday() + 1  # 1=lunes, 7=domingo
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM asistencias WHERE usuario_id=%s AND fecha=%s",(uid,fecha_dia))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM asistencias WHERE id=%s",(existing["id"],))
                conn.commit()
                return jsonify({"message":"Asistencia removida","asistio":False,"fecha":str(fecha_dia)}), 200
            else:
                cur.execute("INSERT INTO asistencias(usuario_id,fecha,dia_semana,registrado_por) VALUES(%s,%s,%s,%s)",
                    (uid,fecha_dia,dia_real,session["user_id"]))
                conn.commit()
                return jsonify({"message":"Asistencia registrada","asistio":True,"id":cur.lastrowid,"fecha":str(fecha_dia)}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()
@app.route("/api/asistencia/<int:aid>/salida", methods=["PUT"])
@login_required
def registrar_salida(aid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE asistencias SET hora_salida=CURRENT_TIME WHERE id=%s",(aid,))
        conn.commit()
        return jsonify({"message":"Salida registrada"}), 200
    finally:
        conn.close()

@app.route("/api/asistencia/reiniciar-semana", methods=["POST"])
@login_required
@role_required("administrador")
def reiniciar_semana():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM asistencias WHERE fecha>=DATE_SUB(CURRENT_DATE,INTERVAL WEEKDAY(CURRENT_DATE) DAY)")
            total = cur.fetchone()["total"]
            cur.execute("INSERT INTO semanas_asistencia(semana_inicio,semana_fin,total_asistencias) VALUES(DATE_SUB(CURRENT_DATE,INTERVAL WEEKDAY(CURRENT_DATE) DAY),DATE_ADD(DATE_SUB(CURRENT_DATE,INTERVAL WEEKDAY(CURRENT_DATE) DAY),INTERVAL 6 DAY),%s)",(total,))
            cur.execute("DELETE FROM asistencias WHERE fecha>=DATE_SUB(CURRENT_DATE,INTERVAL WEEKDAY(CURRENT_DATE) DAY)")
        conn.commit()
        return jsonify({"message":f"Semana reiniciada. {total} registros archivados."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

# ─── MEMBRESÍAS ────────────────────────────────────────────

@app.route("/api/membresias", methods=["GET"])
@login_required
def get_membresias():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM v_membresias_activas")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/membresias/tipos", methods=["GET"])
@login_required
def get_tipos_membresia():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tipos_membresia WHERE activo=1 ORDER BY precio")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/membresias/tipos", methods=["POST"])
@login_required
@role_required("administrador")
def create_tipo_membresia():
    data = request.get_json()
    if not all(data.get(k) for k in ["nombre","precio","duracion_dias"]):
        return jsonify({"error":"Nombre, precio y duración son obligatorios"}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO tipos_membresia(nombre,precio,duracion_dias,descripcion) VALUES(%s,%s,%s,%s)",
                (data["nombre"],data["precio"],data["duracion_dias"],data.get("descripcion")))
        conn.commit()
        return jsonify({"message":"Tipo creado","id":cur.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/membresias/tipos/<int:tid>", methods=["PUT"])
@login_required
@role_required("administrador")
def update_tipo_membresia(tid):
    data = request.get_json()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE tipos_membresia SET nombre=%s,precio=%s,duracion_dias=%s,descripcion=%s WHERE id=%s",
                (data["nombre"],data["precio"],data["duracion_dias"],data.get("descripcion"),tid))
        conn.commit()
        return jsonify({"message":"Actualizado"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/membresias/tipos/<int:tid>", methods=["DELETE"])
@login_required
@role_required("administrador")
def delete_tipo_membresia(tid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE tipos_membresia SET activo=0 WHERE id=%s",(tid,))
        conn.commit()
        return jsonify({"message":"Eliminado"}), 200
    finally:
        conn.close()

@app.route("/api/membresias", methods=["POST"])
@login_required
@role_required("administrador")
def create_membresia():
    data = request.get_json()
    if not all(data.get(k) for k in ["usuario_id","tipo_id","monto_pagado"]):
        return jsonify({"error":"Faltan campos"}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT duracion_dias FROM tipos_membresia WHERE id=%s",(data["tipo_id"],))
            tipo = cur.fetchone()
            if not tipo: return jsonify({"error":"Tipo no encontrado"}), 404
            cur.execute("INSERT INTO membresias(usuario_id,tipo_id,monto_pagado,fecha_fin,observaciones) VALUES(%s,%s,%s,DATE_ADD(CURRENT_DATE,INTERVAL %s DAY),%s)",
                (data["usuario_id"],data["tipo_id"],data["monto_pagado"],tipo["duracion_dias"],data.get("observaciones")))
        conn.commit()
        return jsonify({"message":"Registrada","id":cur.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/membresias/<int:mid>/cancelar", methods=["PUT"])
@login_required
@role_required("administrador")
def cancelar_membresia(mid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE membresias SET estado='cancelada' WHERE id=%s",(mid,))
        conn.commit()
        return jsonify({"message":"Cancelada"}), 200
    finally:
        conn.close()

@app.route("/api/membresias/<int:mid>/reactivar", methods=["PUT"])
@login_required
@role_required("administrador")
def reactivar_membresia(mid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tipo_id FROM membresias WHERE id=%s",(mid,))
            mb = cur.fetchone()
            if not mb: return jsonify({"error":"No encontrada"}), 404
            cur.execute("SELECT duracion_dias FROM tipos_membresia WHERE id=%s",(mb["tipo_id"],))
            tipo = cur.fetchone()
            cur.execute("UPDATE membresias SET estado='activa',fecha_inicio=CURRENT_DATE,fecha_fin=DATE_ADD(CURRENT_DATE,INTERVAL %s DAY) WHERE id=%s",
                (tipo["duracion_dias"],mid))
        conn.commit()
        return jsonify({"message":"Membresía reactivada"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/membresias/<int:mid>/congelar", methods=["PUT"])
@login_required
@role_required("administrador")
def congelar_membresia(mid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE membresias SET estado='congelada',fecha_congelacion=CURRENT_DATE WHERE id=%s AND estado='activa'",(mid,))
            if cur.rowcount==0: return jsonify({"error":"Solo se puede congelar una membresía activa"}), 400
        conn.commit()
        return jsonify({"message":"Membresía congelada ❄"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/membresias/<int:mid>/descongelar", methods=["PUT"])
@login_required
@role_required("administrador")
def descongelar_membresia(mid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT fecha_congelacion,fecha_fin FROM membresias WHERE id=%s AND estado='congelada'",(mid,))
            mb = cur.fetchone()
            if not mb: return jsonify({"error":"Membresía no está congelada"}), 400
            dias = (date.today() - mb["fecha_congelacion"]).days
            cur.execute("UPDATE membresias SET estado='activa',fecha_fin=DATE_ADD(fecha_fin,INTERVAL %s DAY),dias_congelados=dias_congelados+%s,fecha_congelacion=NULL WHERE id=%s",
                (dias,dias,mid))
        conn.commit()
        return jsonify({"message":f"Descongelada. Se extendieron {dias} día(s)."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/membresias/resumen", methods=["GET"])
@login_required
@role_required("administrador")
def resumen_membresias():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT COUNT(*) AS total,
                SUM(CASE WHEN estado='activa' THEN 1 ELSE 0 END) AS activas,
                SUM(CASE WHEN estado='vencida' THEN 1 ELSE 0 END) AS vencidas,
                SUM(CASE WHEN estado='cancelada' THEN 1 ELSE 0 END) AS canceladas,
                SUM(CASE WHEN estado='congelada' THEN 1 ELSE 0 END) AS congeladas,
                SUM(CASE WHEN estado='activa' THEN monto_pagado ELSE 0 END) AS ingresos_activos,
                SUM(CASE WHEN DATEDIFF(fecha_fin,CURRENT_DATE) BETWEEN 0 AND 7 AND estado='activa' THEN 1 ELSE 0 END) AS proximas_vencer
                FROM membresias""")
            return jsonify(cur.fetchone()), 200
    finally:
        conn.close()

# ─── PERFIL ────────────────────────────────────────────────

@app.route("/api/perfil", methods=["GET"])
@login_required
def get_perfil():
    uid = session["user_id"]
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT u.id,u.cedula,u.nombre,u.apellido,u.email,u.telefono,u.genero,
                CAST(u.fecha_nacimiento AS CHAR) AS fecha_nacimiento,
                CAST(u.fecha_registro AS CHAR) AS fecha_registro,
                u.estado,r.nombre AS rol
                FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.id=%s""",(uid,))
            user = cur.fetchone()
            cur.execute("SELECT * FROM v_miembros_rutinas WHERE usuario_id=%s",(uid,))
            rutina = cur.fetchone()
            if rutina and rutina.get("rutina_id"):
                cur.execute("SELECT * FROM ejercicios WHERE rutina_id=%s ORDER BY dia,id",(rutina["rutina_id"],))
                rutina["ejercicios"] = cur.fetchall()
            cur.execute("SELECT * FROM v_asistencia_mensual WHERE usuario_id=%s ORDER BY anio DESC,mes DESC LIMIT 6",(uid,))
            asist = cur.fetchall()
            cur.execute("SELECT * FROM v_membresias_activas WHERE email=%s AND estado IN('activa','congelada') ORDER BY fecha_fin DESC LIMIT 1",(user["email"],))
            membresia = cur.fetchone()
            cur.execute("SELECT * FROM valoraciones_fisicas WHERE usuario_id=%s ORDER BY id DESC LIMIT 1",(uid,))
            fisica = cur.fetchone()
            if fisica:
                cur.execute("SELECT * FROM fotos_valoracion WHERE valoracion_id=%s",(fisica["id"],))
                fisica["fotos"] = cur.fetchall()
        return jsonify({"usuario":user,"rutina":rutina,"asistencia_mensual":asist,"membresia":membresia,"fisica":fisica}), 200
    finally:
        conn.close()

@app.route("/api/perfil", methods=["PUT"])
@login_required
def update_perfil():
    data = request.get_json()
    uid = session["user_id"]
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET nombre=%s,apellido=%s,telefono=%s WHERE id=%s",
                (data.get("nombre"),data.get("apellido"),data.get("telefono"),uid))
            if data.get("password"):
                hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
                cur.execute("UPDATE usuarios SET password_hash=%s WHERE id=%s",(hashed,uid))
        conn.commit()
        session["nombre"]=f"{data.get('nombre','')} {data.get('apellido','')}".strip()
        return jsonify({"message":"Actualizado"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

# ─── HORARIOS ──────────────────────────────────────────────

@app.route("/api/horarios", methods=["GET"])
@login_required
def get_horarios():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM v_horarios")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/horarios", methods=["POST"])
@login_required
@role_required("administrador","entrenador")
def create_horario():
    data = request.get_json()
    if not all(data.get(k) for k in ["nombre","hora_inicio","hora_fin","dias"]):
        return jsonify({"error":"Nombre, hora inicio, hora fin y días son obligatorios"}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO horarios(nombre,hora_inicio,hora_fin,dias,cupo_max,entrenador_id,tipo) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (data["nombre"],data["hora_inicio"],data["hora_fin"],data["dias"],data.get("cupo_max",20),data.get("entrenador_id") or None,data.get("tipo","clase")))
        conn.commit()
        return jsonify({"message":"Horario creado","id":cur.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/horarios/<int:hid>", methods=["PUT"])
@login_required
@role_required("administrador","entrenador")
def update_horario(hid):
    data = request.get_json()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE horarios SET nombre=%s,hora_inicio=%s,hora_fin=%s,dias=%s,cupo_max=%s,entrenador_id=%s,tipo=%s WHERE id=%s",
                (data["nombre"],data["hora_inicio"],data["hora_fin"],data["dias"],data.get("cupo_max",20),data.get("entrenador_id") or None,data.get("tipo","clase"),hid))
        conn.commit()
        return jsonify({"message":"Actualizado"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/horarios/<int:hid>", methods=["DELETE"])
@login_required
@role_required("administrador")
def delete_horario(hid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE horarios SET activo=0 WHERE id=%s",(hid,))
        conn.commit()
        return jsonify({"message":"Eliminado"}), 200
    finally:
        conn.close()

@app.route("/api/horarios/reservar", methods=["POST"])
@login_required
def reservar_horario():
    data = request.get_json()
    usuario_id = data.get("usuario_id") or session["user_id"]
    horario_id = data.get("horario_id")
    fecha = data.get("fecha") or str(date.today())
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO reservas_horario(usuario_id,horario_id,fecha,reservado_por) VALUES(%s,%s,%s,%s)",
                (usuario_id,horario_id,fecha,session["user_id"]))
        conn.commit()
        return jsonify({"message":"Reservado"}), 201
    except Exception as e:
        conn.rollback()
        if "Duplicate" in str(e): return jsonify({"error":"Ya tienes esta clase reservada para ese día"}), 400
        return jsonify({"error":str(e)}), 400
    finally:
        conn.close()

@app.route("/api/horarios/reservar/cancelar", methods=["PUT"])
@login_required
def cancelar_reserva():
    data = request.get_json()
    uid = data.get("usuario_id") or session["user_id"]
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE reservas_horario SET estado='cancelada' WHERE usuario_id=%s AND horario_id=%s AND fecha=%s",
                (uid,data.get("horario_id"),data.get("fecha")))
        conn.commit()
        return jsonify({"message":"Cancelada"}), 200
    finally:
        conn.close()

@app.route("/api/horarios/mis-reservas", methods=["GET"])
@login_required
def mis_reservas():
    uid = session["user_id"]
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT r.*,h.nombre,TIME_FORMAT(h.hora_inicio,'%H:%i') AS hora_inicio,
                TIME_FORMAT(h.hora_fin,'%H:%i') AS hora_fin,h.dias,h.tipo,CAST(r.fecha AS CHAR) AS fecha
                FROM reservas_horario r JOIN horarios h ON h.id=r.horario_id
                WHERE r.usuario_id=%s AND r.fecha>=CURRENT_DATE AND r.estado='confirmada'
                ORDER BY r.fecha,h.hora_inicio""",(uid,))
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/horarios/<int:hid>/miembros", methods=["GET"])
@login_required
@role_required("administrador","entrenador")
def miembros_por_horario(hid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT CONCAT(u.nombre,' ',u.apellido) AS miembro,u.email,
                r.nombre AS rutina,r.nivel,CONCAT(e.nombre,' ',e.apellido) AS entrenador,
                CAST(a.fecha_inicio AS CHAR) AS fecha_inicio
                FROM asignaciones a JOIN usuarios u ON u.id=a.usuario_id
                JOIN rutinas r ON r.id=a.rutina_id JOIN entrenadores e ON e.id=a.entrenador_id
                WHERE a.estado='activa' AND u.estado='activo' ORDER BY u.nombre""")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

# ─── REPORTES ──────────────────────────────────────────────

@app.route("/api/reportes/miembros-rutinas", methods=["GET"])
@login_required
@role_required("administrador","entrenador")
def reporte_miembros_rutinas():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM v_miembros_rutinas")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/reportes/asistencia-mensual", methods=["GET"])
@login_required
def reporte_asistencia_mensual():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM v_asistencia_mensual ORDER BY anio DESC,mes DESC")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/reportes/carga-entrenadores", methods=["GET"])
@login_required
@role_required("administrador","entrenador")
def reporte_carga_entrenadores():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM v_carga_entrenadores")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/reportes/auditoria", methods=["GET"])
@login_required
@role_required("administrador")
def reporte_auditoria():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM auditoria_log ORDER BY fecha DESC LIMIT 100")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

@app.route("/api/roles", methods=["GET"])
@login_required
def get_roles():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM roles")
            return jsonify(cur.fetchall()), 200
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
