═══════════════════════════════════════════════════════
  GymPro v6 — Sistema de Gestión de Gimnasios
═══════════════════════════════════════════════════════

INSTALACIÓN:
1. Abrir MySQL Workbench → borrar BD "gympro" si existe
2. Ejecutar database/gympro.sql completo
3. En VS Code: 
   python -m venv venv
   venv\Scripts\activate        (Windows)
   pip install -r requirements.txt
4. python setup_admin.py
5. python app.py → http://localhost:5000

CREDENCIALES:
  Admin:       admin@gympro.com        / Admin1234!
  Miembros:    juan@gmail.com etc.     / Miembro123!
  Entrenadores:carlos.e@gympro.com etc./ Entrena123!

NOVEDADES v6:
  ✅ Valoración física completa (evaluador, antropometría,
     composición corporal, perímetros, fotos)
  ✅ Rutina solo si valoración completa
  ✅ Cédula validada al crear usuario
  ✅ Entrenadores con login propio + panel asistencia
  ✅ Asistencia semanal con botón por día (Lun-Dom)
  ✅ Clic derecho en día = ver ejercicios del día
  ✅ Horarios: CRUD completo (admin) + reserva con calendario
  ✅ Asistencia sincronizada miembro ↔ entrenador/admin
  ✅ Membresías: congelar, descongelar, reactivar,
     agregar/eliminar tipos de plan
  ✅ Todo permanece en BD (historial nunca se borra)
