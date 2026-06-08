-- ============================================================
--  GymPro v6 — Base de Datos Completa
-- ============================================================
CREATE DATABASE IF NOT EXISTS gympro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gympro;

CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    cedula        VARCHAR(20) NOT NULL UNIQUE,
    nombre        VARCHAR(100) NOT NULL,
    apellido      VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    telefono      VARCHAR(20),
    fecha_nacimiento DATE,
    genero        ENUM('masculino','femenino','otro'),
    fecha_registro DATE NOT NULL DEFAULT (CURRENT_DATE),
    estado        ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
    rol_id        INT NOT NULL,
    CONSTRAINT fk_usuario_rol FOREIGN KEY (rol_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS entrenadores (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    cedula          VARCHAR(20) NOT NULL UNIQUE,
    nombre          VARCHAR(100) NOT NULL,
    apellido        VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255),
    especialidad    VARCHAR(150),
    telefono        VARCHAR(20),
    titulo          VARCHAR(200) COMMENT 'Título profesional',
    universidad     VARCHAR(200) COMMENT 'Universidad o institución',
    es_profesional  TINYINT(1) DEFAULT 0,
    anos_experiencia INT DEFAULT 0,
    certificaciones TEXT,
    estado          ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
    fecha_ingreso   DATE NOT NULL DEFAULT (CURRENT_DATE)
);

-- Valoración física completa
CREATE TABLE IF NOT EXISTS valoraciones_fisicas (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id              INT NOT NULL,
    evaluador_id            INT COMMENT 'ID del entrenador que realizó la valoración',
    evaluador_nombre        VARCHAR(200) COMMENT 'Nombre del evaluador',
    fecha_valoracion        DATE NOT NULL DEFAULT (CURRENT_DATE),
    -- Datos básicos
    fecha_nacimiento        DATE,
    edad                    INT,
    genero                  ENUM('masculino','femenino','otro'),
    -- Antropometría básica
    estatura_cm             DECIMAL(5,1),
    peso_kg                 DECIMAL(5,2),
    imc                     DECIMAL(4,2),
    fc_reposo               INT COMMENT 'Frecuencia cardíaca en reposo (ppm)',
    presion_arterial        VARCHAR(20) COMMENT 'Ej: 120/80 mmHg',
    -- Composición corporal
    porcentaje_grasa        DECIMAL(4,1),
    masa_muscular_kg        DECIMAL(5,2),
    masa_grasa_kg           DECIMAL(5,2),
    grasa_visceral          INT COMMENT 'Escala 1-20',
    porcentaje_agua         DECIMAL(4,1),
    tasa_metabolica_basal   INT COMMENT 'Kcal',
    -- Perímetros corporales (cm)
    perimetro_cuello        DECIMAL(4,1),
    perimetro_hombros       DECIMAL(4,1),
    perimetro_pecho         DECIMAL(4,1),
    perimetro_cintura       DECIMAL(4,1),
    perimetro_cadera        DECIMAL(4,1),
    perimetro_brazo_izq_rel DECIMAL(4,1) COMMENT 'Brazo izquierdo relajado',
    perimetro_brazo_izq_con DECIMAL(4,1) COMMENT 'Brazo izquierdo contraído',
    perimetro_brazo_der_rel DECIMAL(4,1) COMMENT 'Brazo derecho relajado',
    perimetro_brazo_der_con DECIMAL(4,1) COMMENT 'Brazo derecho contraído',
    perimetro_muslo_izq_alt DECIMAL(4,1) COMMENT 'Muslo izquierdo parte alta',
    perimetro_muslo_izq_med DECIMAL(4,1) COMMENT 'Muslo izquierdo parte media',
    perimetro_muslo_der_alt DECIMAL(4,1) COMMENT 'Muslo derecho parte alta',
    perimetro_muslo_der_med DECIMAL(4,1) COMMENT 'Muslo derecho parte media',
    perimetro_pantorrilla_izq DECIMAL(4,1),
    perimetro_pantorrilla_der DECIMAL(4,1),
    -- Salud
    enfermedades            TEXT,
    lesiones                TEXT,
    medicamentos            TEXT,
    fumador                 TINYINT(1) DEFAULT 0,
    objetivo                ENUM('bajar_peso','ganar_musculo','mantener','mejorar_salud','aumentar_resistencia') DEFAULT 'mantener',
    nivel_actividad         ENUM('sedentario','poco_activo','activo','muy_activo') DEFAULT 'poco_activo',
    observaciones           TEXT,
    completada              TINYINT(1) DEFAULT 0 COMMENT '1 si tiene suficientes datos para asignar rutina',
    fecha_registro          DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_val_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Fotos de valoración
CREATE TABLE IF NOT EXISTS fotos_valoracion (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    valoracion_id   INT NOT NULL,
    usuario_id      INT NOT NULL,
    tipo            ENUM('frente','espalda','lateral_izq','lateral_der','otro') DEFAULT 'otro',
    ruta_archivo    VARCHAR(500) NOT NULL,
    fecha_subida    DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_foto_val FOREIGN KEY (valoracion_id) REFERENCES valoraciones_fisicas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rutinas (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    nombre           VARCHAR(150) NOT NULL,
    descripcion      TEXT,
    objetivo         ENUM('fuerza','cardio','flexibilidad','perdida_peso','ganancia_muscular','general') NOT NULL DEFAULT 'general',
    duracion_semanas INT NOT NULL DEFAULT 4,
    nivel            ENUM('principiante','intermedio','avanzado') NOT NULL DEFAULT 'principiante',
    dias_por_semana  INT NOT NULL DEFAULT 3,
    entrenador_id    INT NOT NULL,
    fecha_creacion   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rutina_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id)
);

CREATE TABLE IF NOT EXISTS ejercicios (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    rutina_id    INT NOT NULL,
    nombre       VARCHAR(150) NOT NULL,
    series       INT NOT NULL DEFAULT 3,
    repeticiones VARCHAR(20) NOT NULL DEFAULT '10',
    descanso_seg INT NOT NULL DEFAULT 60,
    dia          INT NOT NULL DEFAULT 1,
    notas        TEXT,
    CONSTRAINT fk_ejercicio_rutina FOREIGN KEY (rutina_id) REFERENCES rutinas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS asignaciones (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id    INT NOT NULL,
    rutina_id     INT NOT NULL,
    entrenador_id INT NOT NULL,
    fecha_inicio  DATE NOT NULL DEFAULT (CURRENT_DATE),
    fecha_fin     DATE,
    estado        ENUM('activa','completada','cancelada') NOT NULL DEFAULT 'activa',
    observaciones TEXT,
    CONSTRAINT fk_asig_usuario    FOREIGN KEY (usuario_id)    REFERENCES usuarios(id),
    CONSTRAINT fk_asig_rutina     FOREIGN KEY (rutina_id)     REFERENCES rutinas(id),
    CONSTRAINT fk_asig_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id)
);

CREATE TABLE IF NOT EXISTS asistencias (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    fecha           DATE NOT NULL DEFAULT (CURRENT_DATE),
    dia_semana      TINYINT NOT NULL DEFAULT 1 COMMENT '1=Lunes...7=Domingo',
    hora_entrada    TIME NOT NULL DEFAULT (CURRENT_TIME),
    hora_salida     TIME,
    registrado_por  INT COMMENT 'ID admin/entrenador que marcó',
    observacion     VARCHAR(255),
    CONSTRAINT fk_asist_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    CONSTRAINT uq_asistencia_dia UNIQUE (usuario_id, fecha)
);

CREATE TABLE IF NOT EXISTS semanas_asistencia (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    semana_inicio    DATE NOT NULL,
    semana_fin       DATE NOT NULL,
    archivado_en     DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_asistencias INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tipos_membresia (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    precio        DECIMAL(10,2) NOT NULL,
    duracion_dias INT NOT NULL DEFAULT 30,
    descripcion   TEXT,
    activo        TINYINT(1) DEFAULT 1
);

CREATE TABLE IF NOT EXISTS membresias (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id        INT NOT NULL,
    tipo_id           INT NOT NULL,
    fecha_inicio      DATE NOT NULL DEFAULT (CURRENT_DATE),
    fecha_fin         DATE NOT NULL,
    estado            ENUM('activa','vencida','cancelada','congelada') NOT NULL DEFAULT 'activa',
    monto_pagado      DECIMAL(10,2) NOT NULL,
    fecha_pago        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_congelacion DATE,
    dias_congelados   INT DEFAULT 0,
    observaciones     TEXT,
    CONSTRAINT fk_memb_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    CONSTRAINT fk_memb_tipo    FOREIGN KEY (tipo_id)    REFERENCES tipos_membresia(id)
);

CREATE TABLE IF NOT EXISTS horarios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    hora_inicio   TIME NOT NULL,
    hora_fin      TIME NOT NULL,
    dias          VARCHAR(50) NOT NULL,
    cupo_max      INT NOT NULL DEFAULT 20,
    entrenador_id INT,
    tipo          ENUM('general','clase','personal') NOT NULL DEFAULT 'general',
    activo        TINYINT(1) DEFAULT 1,
    CONSTRAINT fk_horario_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id)
);

CREATE TABLE IF NOT EXISTS reservas_horario (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    horario_id INT NOT NULL,
    fecha      DATE NOT NULL DEFAULT (CURRENT_DATE),
    estado     ENUM('confirmada','cancelada') NOT NULL DEFAULT 'confirmada',
    reservado_por INT COMMENT 'Admin que hizo la reserva si fue manual',
    CONSTRAINT fk_reserva_usuario FOREIGN KEY (usuario_id)  REFERENCES usuarios(id),
    CONSTRAINT fk_reserva_horario FOREIGN KEY (horario_id)  REFERENCES horarios(id),
    CONSTRAINT uq_reserva UNIQUE (usuario_id, horario_id, fecha)
);

CREATE TABLE IF NOT EXISTS auditoria_log (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    tabla      VARCHAR(100) NOT NULL,
    operacion  ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    registro_id INT NOT NULL,
    detalle    TEXT,
    usuario_id INT,
    fecha      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- VISTAS
-- ============================================================

CREATE OR REPLACE VIEW v_asistencia_semana AS
SELECT u.id AS usuario_id,
       u.cedula,
       CONCAT(u.nombre,' ',u.apellido) AS miembro,
       u.email,
       MAX(CASE WHEN a.dia_semana=1 THEN a.id ELSE NULL END) AS lun_id,
       MAX(CASE WHEN a.dia_semana=1 THEN TIME_FORMAT(a.hora_entrada,'%H:%i') ELSE NULL END) AS lun_hora,
       MAX(CASE WHEN a.dia_semana=2 THEN a.id ELSE NULL END) AS mar_id,
       MAX(CASE WHEN a.dia_semana=2 THEN TIME_FORMAT(a.hora_entrada,'%H:%i') ELSE NULL END) AS mar_hora,
       MAX(CASE WHEN a.dia_semana=3 THEN a.id ELSE NULL END) AS mie_id,
       MAX(CASE WHEN a.dia_semana=3 THEN TIME_FORMAT(a.hora_entrada,'%H:%i') ELSE NULL END) AS mie_hora,
       MAX(CASE WHEN a.dia_semana=4 THEN a.id ELSE NULL END) AS jue_id,
       MAX(CASE WHEN a.dia_semana=4 THEN TIME_FORMAT(a.hora_entrada,'%H:%i') ELSE NULL END) AS jue_hora,
       MAX(CASE WHEN a.dia_semana=5 THEN a.id ELSE NULL END) AS vie_id,
       MAX(CASE WHEN a.dia_semana=5 THEN TIME_FORMAT(a.hora_entrada,'%H:%i') ELSE NULL END) AS vie_hora,
       MAX(CASE WHEN a.dia_semana=6 THEN a.id ELSE NULL END) AS sab_id,
       MAX(CASE WHEN a.dia_semana=6 THEN TIME_FORMAT(a.hora_entrada,'%H:%i') ELSE NULL END) AS sab_hora,
       MAX(CASE WHEN a.dia_semana=7 THEN a.id ELSE NULL END) AS dom_id,
       MAX(CASE WHEN a.dia_semana=7 THEN TIME_FORMAT(a.hora_entrada,'%H:%i') ELSE NULL END) AS dom_hora
FROM usuarios u
LEFT JOIN asistencias a ON a.usuario_id=u.id
    AND a.fecha>=DATE_SUB(CURRENT_DATE,INTERVAL WEEKDAY(CURRENT_DATE) DAY)
    AND a.fecha<=DATE_ADD(DATE_SUB(CURRENT_DATE,INTERVAL WEEKDAY(CURRENT_DATE) DAY),INTERVAL 6 DAY)
WHERE u.rol_id=(SELECT id FROM roles WHERE nombre='miembro') AND u.estado='activo'
GROUP BY u.id ORDER BY u.nombre;

CREATE OR REPLACE VIEW v_asistencia_hoy AS
SELECT u.id AS usuario_id, u.cedula,
       CONCAT(u.nombre,' ',u.apellido) AS miembro, u.email,
       CASE WHEN a.id IS NOT NULL THEN 'SI' ELSE 'NO' END AS asistio,
       a.id AS asistencia_id,
       TIME_FORMAT(a.hora_entrada,'%H:%i') AS hora_entrada,
       TIME_FORMAT(a.hora_salida,'%H:%i')  AS hora_salida
FROM usuarios u
LEFT JOIN asistencias a ON a.usuario_id=u.id AND a.fecha=CURRENT_DATE
WHERE u.rol_id=(SELECT id FROM roles WHERE nombre='miembro') AND u.estado='activo'
ORDER BY u.nombre;

CREATE OR REPLACE VIEW v_asistencia_detalle AS
SELECT u.id AS usuario_id,
       CONCAT(u.nombre,' ',u.apellido) AS miembro,
       a.id, a.fecha, a.dia_semana,
       TIME_FORMAT(a.hora_entrada,'%H:%i') AS hora_entrada,
       TIME_FORMAT(a.hora_salida,'%H:%i')  AS hora_salida,
       CASE WHEN a.hora_salida IS NOT NULL
            THEN TIME_FORMAT(TIMEDIFF(a.hora_salida,a.hora_entrada),'%H:%i')
            ELSE NULL END AS tiempo_gym
FROM asistencias a JOIN usuarios u ON u.id=a.usuario_id
ORDER BY a.fecha DESC;

CREATE OR REPLACE VIEW v_asistencia_mensual AS
SELECT u.id AS usuario_id, CONCAT(u.nombre,' ',u.apellido) AS miembro,
       YEAR(a.fecha) AS anio, MONTH(a.fecha) AS mes, COUNT(*) AS total_asistencias
FROM asistencias a JOIN usuarios u ON u.id=a.usuario_id
GROUP BY u.id, YEAR(a.fecha), MONTH(a.fecha);

CREATE OR REPLACE VIEW v_membresias_activas AS
SELECT m.id, CONCAT(u.nombre,' ',u.apellido) AS miembro,
       u.email, u.cedula, t.nombre AS tipo_membresia,
       t.precio, m.monto_pagado,
       CAST(m.fecha_inicio AS CHAR) AS fecha_inicio,
       CAST(m.fecha_fin AS CHAR) AS fecha_fin,
       DATEDIFF(m.fecha_fin,CURRENT_DATE) AS dias_restantes,
       m.estado, m.dias_congelados,
       CAST(m.fecha_congelacion AS CHAR) AS fecha_congelacion
FROM membresias m
JOIN usuarios u ON u.id=m.usuario_id
JOIN tipos_membresia t ON t.id=m.tipo_id
ORDER BY m.fecha_fin ASC;

CREATE OR REPLACE VIEW v_miembros_rutinas AS
SELECT u.id AS usuario_id, CONCAT(u.nombre,' ',u.apellido) AS miembro,
       u.email, u.estado AS estado_miembro,
       r.id AS rutina_id, r.nombre AS rutina,
       r.objetivo, r.nivel, r.duracion_semanas, r.dias_por_semana,
       CONCAT(e.nombre,' ',e.apellido) AS entrenador,
       a.id AS asignacion_id,
       CAST(a.fecha_inicio AS CHAR) AS fecha_inicio,
       a.estado AS estado_asignacion
FROM usuarios u
LEFT JOIN asignaciones a ON a.usuario_id=u.id AND a.estado='activa'
LEFT JOIN rutinas r ON r.id=a.rutina_id
LEFT JOIN entrenadores e ON e.id=a.entrenador_id
WHERE u.rol_id=(SELECT id FROM roles WHERE nombre='miembro');

CREATE OR REPLACE VIEW v_horarios AS
SELECT h.id, h.nombre,
       TIME_FORMAT(h.hora_inicio,'%H:%i') AS hora_inicio,
       TIME_FORMAT(h.hora_fin,'%H:%i')    AS hora_fin,
       h.dias, h.cupo_max, h.tipo, h.activo,
       IFNULL(CONCAT(e.nombre,' ',e.apellido),'Sin entrenador') AS entrenador,
       h.entrenador_id,
       (SELECT COUNT(*) FROM reservas_horario r
        WHERE r.horario_id=h.id AND r.fecha=CURRENT_DATE AND r.estado='confirmada') AS reservas_hoy
FROM horarios h
LEFT JOIN entrenadores e ON e.id=h.entrenador_id
WHERE h.activo=1
ORDER BY h.hora_inicio;

CREATE OR REPLACE VIEW v_carga_entrenadores AS
SELECT e.id, CONCAT(e.nombre,' ',e.apellido) AS entrenador, e.especialidad,
       COUNT(DISTINCT r.id) AS total_rutinas,
       COUNT(DISTINCT a.usuario_id) AS miembros_activos
FROM entrenadores e
LEFT JOIN rutinas r ON r.entrenador_id=e.id
LEFT JOIN asignaciones a ON a.entrenador_id=e.id AND a.estado='activa'
GROUP BY e.id;

-- ============================================================
-- TRIGGERS
-- ============================================================
DELIMITER $$
CREATE TRIGGER trg_asistencia_dia
BEFORE INSERT ON asistencias FOR EACH ROW
BEGIN
    SET NEW.dia_semana = CASE DAYOFWEEK(CURRENT_DATE)
        WHEN 2 THEN 1 WHEN 3 THEN 2 WHEN 4 THEN 3
        WHEN 5 THEN 4 WHEN 6 THEN 5 WHEN 7 THEN 6 ELSE 7
    END;
    IF NEW.fecha IS NULL THEN SET NEW.fecha = CURRENT_DATE; END IF;
END$$

CREATE TRIGGER trg_usuarios_insert
AFTER INSERT ON usuarios FOR EACH ROW
BEGIN
    INSERT INTO auditoria_log(tabla,operacion,registro_id,detalle,usuario_id)
    VALUES('usuarios','INSERT',NEW.id,CONCAT('Nuevo: ',NEW.nombre,' ',NEW.apellido,' CC:',NEW.cedula),NEW.id);
END$$

CREATE TRIGGER trg_valoracion_completada
BEFORE INSERT ON valoraciones_fisicas FOR EACH ROW
BEGIN
    IF NEW.estatura_cm IS NOT NULL AND NEW.peso_kg IS NOT NULL
       AND NEW.porcentaje_grasa IS NOT NULL AND NEW.perimetro_cintura IS NOT NULL
    THEN SET NEW.completada = 1;
    ELSE SET NEW.completada = 0;
    END IF;
END$$

CREATE TRIGGER trg_valoracion_update
BEFORE UPDATE ON valoraciones_fisicas FOR EACH ROW
BEGIN
    IF NEW.estatura_cm IS NOT NULL AND NEW.peso_kg IS NOT NULL
       AND NEW.porcentaje_grasa IS NOT NULL AND NEW.perimetro_cintura IS NOT NULL
    THEN SET NEW.completada = 1;
    ELSE SET NEW.completada = 0;
    END IF;
END$$
DELIMITER ;

-- ============================================================
-- DATOS INICIALES
-- ============================================================
INSERT INTO roles(nombre) VALUES('administrador'),('entrenador'),('miembro');

INSERT INTO tipos_membresia(nombre,precio,duracion_dias,descripcion,activo) VALUES
('Mensual Básico',   50000,  30, 'Acceso básico lunes a sábado',1),
('Mensual Premium',  80000,  30, 'Acceso completo con clases incluidas',1),
('Trimestral',      140000,  90, 'Ahorra 15% pagando 3 meses',1),
('Semestral',       250000, 180, 'El mejor precio para comprometidos',1),
('Anual',           500000, 365, 'Acceso ilimitado todo el año',1);

INSERT INTO usuarios(cedula,nombre,apellido,email,password_hash,telefono,fecha_nacimiento,genero,rol_id,fecha_registro)
VALUES('0000000000','Admin','GymPro','admin@gympro.com','$2b$12$placeholder','3001234567','1990-01-01','masculino',1,DATE_SUB(CURRENT_DATE,INTERVAL 365 DAY));

INSERT INTO entrenadores(cedula,nombre,apellido,email,password_hash,especialidad,telefono,titulo,es_profesional,anos_experiencia,fecha_ingreso) VALUES
('1001001001','Carlos',   'Mendoza', 'carlos.e@gympro.com','$2b$12$placeholder','Fuerza y musculación',   '3101234001','Licenciado en Educación Física',1,8,DATE_SUB(CURRENT_DATE,INTERVAL 300 DAY)),
('1001001002','Laura',    'Pérez',   'laura.e@gympro.com', '$2b$12$placeholder','Cardio y pérdida de peso','3101234002','Entrenador Personal Certificado',1,5,DATE_SUB(CURRENT_DATE,INTERVAL 280 DAY)),
('1001001003','Roberto',  'Salinas', 'roberto.e@gympro.com','$2b$12$placeholder','Flexibilidad y yoga',   '3101234003','Instructor de Yoga Certificado',1,6,DATE_SUB(CURRENT_DATE,INTERVAL 250 DAY)),
('1001001004','Valentina','Torres',  'vale.e@gympro.com',  '$2b$12$placeholder','CrossFit y funcional',   '3101234004','CrossFit Level 2 Trainer',1,4,DATE_SUB(CURRENT_DATE,INTERVAL 180 DAY)),
('1001001005','Andrés',   'Gutiérrez','andres.e@gympro.com','$2b$12$placeholder','Nutrición deportiva',   '3101234005','Nutricionista Deportivo',1,3,DATE_SUB(CURRENT_DATE,INTERVAL 120 DAY));

INSERT INTO usuarios(cedula,nombre,apellido,email,password_hash,telefono,fecha_nacimiento,genero,rol_id,fecha_registro) VALUES
('1090001001','Juan',     'Martínez', 'juan@gmail.com',      '$2b$12$placeholder','3201110001','1996-05-15','masculino',3,DATE_SUB(CURRENT_DATE,INTERVAL 180 DAY)),
('1090001002','María',    'González', 'maria@gmail.com',     '$2b$12$placeholder','3201110002','1992-08-22','femenino', 3,DATE_SUB(CURRENT_DATE,INTERVAL 150 DAY)),
('1090001003','Carlos',   'Rodríguez','carlos@gmail.com',    '$2b$12$placeholder','3201110003','1999-03-10','masculino',3,DATE_SUB(CURRENT_DATE,INTERVAL 120 DAY)),
('1090001004','Ana',      'López',    'ana@gmail.com',       '$2b$12$placeholder','3201110004','1979-11-30','femenino', 3,DATE_SUB(CURRENT_DATE,INTERVAL 100 DAY)),
('1090001005','Pedro',    'Sánchez',  'pedro@gmail.com',     '$2b$12$placeholder','3201110005','2002-07-04','masculino',3,DATE_SUB(CURRENT_DATE,INTERVAL 90 DAY)),
('1090001006','Sofía',    'Ramírez',  'sofia@gmail.com',     '$2b$12$placeholder','3201110006','1991-02-18','femenino', 3,DATE_SUB(CURRENT_DATE,INTERVAL 75 DAY)),
('1090001007','Diego',    'Herrera',  'diego@gmail.com',     '$2b$12$placeholder','3201110007','1995-09-25','masculino',3,DATE_SUB(CURRENT_DATE,INTERVAL 60 DAY)),
('1090001008','Valentina','Castro',   'valentina@gmail.com', '$2b$12$placeholder','3201110008','1997-12-01','femenino', 3,DATE_SUB(CURRENT_DATE,INTERVAL 45 DAY)),
('1090001009','Andrés',   'Moreno',   'andres@gmail.com',    '$2b$12$placeholder','3201110009','2000-06-14','masculino',3,DATE_SUB(CURRENT_DATE,INTERVAL 30 DAY)),
('1090001010','Isabella', 'Jiménez',  'isabella@gmail.com',  '$2b$12$placeholder','3201110010','1986-04-07','femenino', 3,DATE_SUB(CURRENT_DATE,INTERVAL 20 DAY));

-- Valoraciones físicas de ejemplo (completas para poder asignar rutinas)
INSERT INTO valoraciones_fisicas(usuario_id,evaluador_nombre,fecha_valoracion,edad,genero,estatura_cm,peso_kg,imc,fc_reposo,presion_arterial,porcentaje_grasa,masa_muscular_kg,masa_grasa_kg,grasa_visceral,porcentaje_agua,tasa_metabolica_basal,perimetro_cuello,perimetro_hombros,perimetro_pecho,perimetro_cintura,perimetro_cadera,objetivo,nivel_actividad,completada) VALUES
(2, 'Carlos Mendoza',DATE_SUB(CURRENT_DATE,INTERVAL 150 DAY),28,'masculino',175.0,78.5,25.6,68,'120/80',22.5,45.2,17.6,8,58.3,1820,38.5,112.0,96.0,82.0,95.0,'bajar_peso','poco_activo',1),
(3, 'Laura Pérez',   DATE_SUB(CURRENT_DATE,INTERVAL 120 DAY),32,'femenino', 163.0,62.0,23.3,72,'110/75',28.2,33.8,17.5,6,55.1,1380,33.0,98.0, 88.0,70.0,96.0,'mantener','activo',1),
(4, 'Carlos Mendoza',DATE_SUB(CURRENT_DATE,INTERVAL 90 DAY), 25,'masculino',180.0,85.0,26.2,65,'118/78',18.0,52.3,15.3,7,62.1,1980,40.0,118.0,103.0,85.0,98.0,'ganar_musculo','activo',1),
(5, 'Andrés Gutiérrez',DATE_SUB(CURRENT_DATE,INTERVAL 80 DAY),45,'masculino',168.0,70.0,24.8,78,'135/85',24.0,40.1,16.8,10,56.8,1650,37.0,108.0,94.0,88.0,96.0,'mejorar_salud','sedentario',1),
(6, 'Laura Pérez',   DATE_SUB(CURRENT_DATE,INTERVAL 65 DAY), 22,'masculino',172.0,90.0,30.4,80,'125/82',32.5,42.0,29.2,14,51.2,1920,41.0,116.0,102.0,95.0,104.0,'bajar_peso','poco_activo',1),
(7, 'Valentina Torres',DATE_SUB(CURRENT_DATE,INTERVAL 60 DAY),35,'femenino',160.0,55.0,21.5,58,'108/70',22.0,32.5,12.1,5,59.8,1280,'','','','62.0',88.0,'aumentar_resistencia','muy_activo',1),
(8, 'Carlos Mendoza',DATE_SUB(CURRENT_DATE,INTERVAL 45 DAY),29,'masculino',183.0,92.0,27.5,70,'122/80',20.5,55.8,18.8,9,60.5,2120,41.5,122.0,108.0,88.0,100.0,'ganar_musculo','activo',1),
(9, 'Andrés Gutiérrez',DATE_SUB(CURRENT_DATE,INTERVAL 35 DAY),41,'femenino',165.0,65.0,23.9,74,'128/82',30.2,35.2,19.6,11,53.5,1320,34.0,100.0,90.0,76.0,100.0,'mantener','poco_activo',1),
(10,'Laura Pérez',   DATE_SUB(CURRENT_DATE,INTERVAL 20 DAY),24,'femenino', 158.0,58.0,23.2,76,'112/74',32.8,29.8,19.0,8,52.1,1250,32.5,96.0, 86.0,72.0,98.0,'bajar_peso','sedentario',1),
(11,'Carlos Mendoza',DATE_SUB(CURRENT_DATE,INTERVAL 15 DAY),38,'masculino',177.0,80.0,25.5,67,'120/78',21.5,48.5,17.2,8,59.2,1880,39.0,114.0,98.0,84.0,97.0,'ganar_musculo','activo',1);

-- Rutinas
INSERT INTO rutinas(nombre,descripcion,objetivo,duracion_semanas,nivel,dias_por_semana,entrenador_id,fecha_creacion) VALUES
('Full Body Principiante','Rutina completa para comenzar.','general',8,'principiante',3,1,DATE_SUB(NOW(),INTERVAL 200 DAY)),
('Quema Grasa Intensiva','Cardio y pesas para máxima quema calórica.','perdida_peso',12,'intermedio',4,2,DATE_SUB(NOW(),INTERVAL 180 DAY)),
('Hipertrofia Máxima','División por grupos musculares.','ganancia_muscular',16,'avanzado',5,1,DATE_SUB(NOW(),INTERVAL 160 DAY)),
('Resistencia Cardiovascular','Mejora capacidad aeróbica.','cardio',8,'intermedio',4,2,DATE_SUB(NOW(),INTERVAL 140 DAY)),
('Yoga y Flexibilidad','Movilidad y reducción del estrés.','flexibilidad',6,'principiante',3,3,DATE_SUB(NOW(),INTERVAL 120 DAY)),
('Glúteos y Piernas','Especializada en piernas y glúteos.','ganancia_muscular',8,'intermedio',3,2,DATE_SUB(NOW(),INTERVAL 100 DAY));

SET @r1=1;
INSERT INTO ejercicios(rutina_id,nombre,series,repeticiones,descanso_seg,dia,notas) VALUES
(@r1,'Sentadilla',3,'15',60,1,'Espalda recta'),(@r1,'Flexiones',3,'10',60,1,'Cuerpo recto'),
(@r1,'Remo mancuerna',3,'12',60,1,'Apoya rodilla'),(@r1,'Plancha',3,'30s',45,1,'Core activo'),
(@r1,'Peso muerto',3,'12',60,2,'Espalda neutra'),(@r1,'Press hombros',3,'12',60,2,'Sentado'),
(@r1,'Curl bíceps',3,'12',45,2,'Codos fijos'),(@r1,'Tríceps polea',3,'12',45,2,'Control bajada'),
(@r1,'Zancadas',3,'10',60,3,'Paso largo'),(@r1,'Elevaciones lat.',3,'12',45,3,'Pesos ligeros'),
(@r1,'Abdominales',3,'20',30,3,'Respirar'),(@r1,'Caminadora',1,'20min',0,3,'Ritmo suave');
SET @r2=2;
INSERT INTO ejercicios(rutina_id,nombre,series,repeticiones,descanso_seg,dia,notas) VALUES
(@r2,'Calentamiento',1,'10min',0,1,'Caminadora'),(@r2,'Burpees',4,'12',45,1,'Explosivo'),
(@r2,'Sentadilla salto',4,'15',45,1,'Aterrizar suave'),(@r2,'Mountain climbers',4,'30s',30,1,'Rápido'),
(@r2,'HIIT bicicleta',1,'20min',0,1,'30s/30s'),(@r2,'Elíptica',1,'30min',0,2,'Ritmo moderado'),
(@r2,'Kettlebell',4,'15',45,3,'Swing'),(@r2,'Cuerda saltar',5,'1min',30,3,'Sin parar'),
(@r2,'Plancha toque',3,'20',45,3,'Cadera estable'),(@r2,'Sentadilla lateral',4,'12',45,4,'Suave'),
(@r2,'Peso muerto rumano',4,'12',60,4,'Isquiotibiales'),(@r2,'Abdominales bici',4,'20',30,4,'Lento');
SET @r3=3;
INSERT INTO ejercicios(rutina_id,nombre,series,repeticiones,descanso_seg,dia,notas) VALUES
(@r3,'Press banca',5,'8-10',90,1,'Pecho'),(@r3,'Press inclinado',4,'10-12',75,1,'30 grados'),
(@r3,'Aperturas',4,'12',60,1,'Arco amplio'),(@r3,'Fondos paralelas',4,'10-15',75,1,'Peso extra'),
(@r3,'Sentadilla',5,'6-8',120,2,'Piernas'),(@r3,'Prensa pierna',4,'10-12',90,2,'No bloquear'),
(@r3,'Curl femoral',4,'12',60,2,'Cadera pegada'),(@r3,'Pantorrillas',5,'15-20',45,2,'Rango completo'),
(@r3,'Peso muerto',5,'5-6',120,3,'Espalda'),(@r3,'Dominadas',4,'8-10',90,3,'Al pecho'),
(@r3,'Remo barra',4,'8-10',90,3,'Codos atrás'),(@r3,'Press militar',5,'8',90,4,'Hombros'),
(@r3,'Elevaciones lat.',4,'12-15',45,4,'Técnica'),(@r3,'Curl barra Z',4,'10',60,5,'Brazos'),
(@r3,'Press francés',4,'10',60,5,'Codos arriba');

-- Asignaciones (manual por entrenador, solo si valoración completa)
INSERT INTO asignaciones(usuario_id,rutina_id,entrenador_id,fecha_inicio,estado,observaciones) VALUES
(2,1,1,DATE_SUB(CURRENT_DATE,INTERVAL 150 DAY),'activa','Valoración completa el día de registro'),
(3,5,3,DATE_SUB(CURRENT_DATE,INTERVAL 120 DAY),'activa','Reducir estrés laboral'),
(4,3,1,DATE_SUB(CURRENT_DATE,INTERVAL 90 DAY), 'activa','Meta competencia en 6 meses'),
(5,4,2,DATE_SUB(CURRENT_DATE,INTERVAL 80 DAY), 'activa','Hipertensión controlada'),
(6,2,2,DATE_SUB(CURRENT_DATE,INTERVAL 65 DAY), 'activa','Bajar 15 kilos'),
(7,4,2,DATE_SUB(CURRENT_DATE,INTERVAL 60 DAY), 'activa','Maratón en 4 meses'),
(8,3,1,DATE_SUB(CURRENT_DATE,INTERVAL 45 DAY), 'activa','Retomando después de pausa'),
(9,6,3,DATE_SUB(CURRENT_DATE,INTERVAL 35 DAY), 'activa','Control glucemia'),
(10,2,2,DATE_SUB(CURRENT_DATE,INTERVAL 20 DAY),'activa','Primera vez'),
(11,6,2,DATE_SUB(CURRENT_DATE,INTERVAL 15 DAY),'activa','Recuperación rodilla');

INSERT INTO membresias(usuario_id,tipo_id,fecha_inicio,fecha_fin,estado,monto_pagado,fecha_pago) VALUES
(2, 2,DATE_SUB(CURRENT_DATE,INTERVAL 15 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 15 DAY),'activa',80000, DATE_SUB(NOW(),INTERVAL 15 DAY)),
(3, 3,DATE_SUB(CURRENT_DATE,INTERVAL 30 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 60 DAY),'activa',140000,DATE_SUB(NOW(),INTERVAL 30 DAY)),
(4, 4,DATE_SUB(CURRENT_DATE,INTERVAL 60 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 120 DAY),'activa',250000,DATE_SUB(NOW(),INTERVAL 60 DAY)),
(5, 1,DATE_SUB(CURRENT_DATE,INTERVAL 10 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 20 DAY),'activa',50000, DATE_SUB(NOW(),INTERVAL 10 DAY)),
(6, 2,DATE_SUB(CURRENT_DATE,INTERVAL 20 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 10 DAY),'activa',80000, DATE_SUB(NOW(),INTERVAL 20 DAY)),
(7, 5,DATE_SUB(CURRENT_DATE,INTERVAL 90 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 275 DAY),'activa',500000,DATE_SUB(NOW(),INTERVAL 90 DAY)),
(8, 3,DATE_SUB(CURRENT_DATE,INTERVAL 45 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 45 DAY),'activa',140000,DATE_SUB(NOW(),INTERVAL 45 DAY)),
(9, 1,DATE_SUB(CURRENT_DATE,INTERVAL 5 DAY), DATE_ADD(CURRENT_DATE,INTERVAL 25 DAY),'activa',50000, DATE_SUB(NOW(),INTERVAL 5 DAY)),
(10,2,DATE_SUB(CURRENT_DATE,INTERVAL 18 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 12 DAY),'activa',80000, DATE_SUB(NOW(),INTERVAL 18 DAY)),
(11,3,DATE_SUB(CURRENT_DATE,INTERVAL 10 DAY),DATE_ADD(CURRENT_DATE,INTERVAL 80 DAY),'activa',140000,DATE_SUB(NOW(),INTERVAL 10 DAY));

-- Asistencias históricas
INSERT INTO asistencias(usuario_id,fecha,dia_semana,hora_entrada,hora_salida) VALUES
(2,DATE_SUB(CURRENT_DATE,INTERVAL 3 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 3 DAY))-1,'06:15:00','07:45:00'),
(2,DATE_SUB(CURRENT_DATE,INTERVAL 6 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 6 DAY))-1,'06:20:00','07:50:00'),
(3,DATE_SUB(CURRENT_DATE,INTERVAL 1 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 1 DAY))-1,'08:00:00','09:00:00'),
(3,DATE_SUB(CURRENT_DATE,INTERVAL 4 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 4 DAY))-1,'08:05:00','09:05:00'),
(4,DATE_SUB(CURRENT_DATE,INTERVAL 2 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 2 DAY))-1,'16:00:00','18:00:00'),
(5,DATE_SUB(CURRENT_DATE,INTERVAL 3 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 3 DAY))-1,'07:00:00','08:00:00'),
(6,DATE_SUB(CURRENT_DATE,INTERVAL 2 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 2 DAY))-1,'06:00:00','07:30:00'),
(7,DATE_SUB(CURRENT_DATE,INTERVAL 1 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 1 DAY))-1,'17:00:00','18:30:00'),
(8,DATE_SUB(CURRENT_DATE,INTERVAL 1 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 1 DAY))-1,'18:00:00','19:30:00'),
(9,DATE_SUB(CURRENT_DATE,INTERVAL 2 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 2 DAY))-1,'07:00:00','08:00:00'),
(10,DATE_SUB(CURRENT_DATE,INTERVAL 2 DAY),DAYOFWEEK(DATE_SUB(CURRENT_DATE,INTERVAL 2 DAY))-1,'09:00:00','10:00:00');

INSERT INTO horarios(nombre,hora_inicio,hora_fin,dias,cupo_max,entrenador_id,tipo) VALUES
('Apertura mañana',        '05:00:00','07:00:00','Lun,Mar,Mie,Jue,Vie,Sab',30,NULL,'general'),
('Entrenamiento funcional','06:00:00','07:00:00','Lun,Mie,Vie',15,1,'clase'),
('Cardio intenso',         '07:00:00','08:00:00','Lun,Mar,Mie,Jue,Vie',20,2,'clase'),
('Zona libre mañana',      '07:00:00','12:00:00','Lun,Mar,Mie,Jue,Vie,Sab',40,NULL,'general'),
('Yoga y flexibilidad',    '08:00:00','09:00:00','Mar,Jue,Sab',12,3,'clase'),
('CrossFit',               '09:00:00','10:00:00','Lun,Mie,Vie',15,4,'clase'),
('Spinning',               '12:00:00','13:00:00','Lun,Mie,Vie',18,2,'clase'),
('Rumba / Zumba',          '17:00:00','18:00:00','Mar,Jue,Sab',25,4,'clase'),
('Zona libre tarde',       '15:00:00','21:00:00','Lun,Mar,Mie,Jue,Vie,Sab',40,NULL,'general'),
('Fuerza y musculación',   '16:00:00','17:00:00','Lun,Mie,Vie',15,1,'clase'),
('Entrenamiento personal', '18:00:00','19:00:00','Lun,Mar,Mie,Jue,Vie',5,1,'personal'),
('Fin de semana',          '08:00:00','13:00:00','Sab,Dom',30,NULL,'general');
