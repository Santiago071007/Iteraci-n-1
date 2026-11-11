PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS novedad;
DROP TABLE IF EXISTS registro_parqueo;
DROP TABLE IF EXISTS mensualidad;
DROP TABLE IF EXISTS vehiculo;
DROP TABLE IF EXISTS cliente;
DROP TABLE IF EXISTS celda;
DROP TABLE IF EXISTS usuario;

CREATE TABLE usuario (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         VARCHAR(100) NOT NULL,
    username       VARCHAR(40)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    rol            VARCHAR(15)  NOT NULL CHECK (rol IN ('ADMIN', 'OPERADOR')),
    activo         INTEGER      NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE cliente (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    documento  VARCHAR(20)  NOT NULL UNIQUE,
    nombres    VARCHAR(120) NOT NULL,
    telefono   VARCHAR(20),
    email      VARCHAR(120)
);

CREATE TABLE vehiculo (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    placa       VARCHAR(6)  NOT NULL UNIQUE,
    tipo        VARCHAR(10) NOT NULL CHECK (tipo IN ('CARRO', 'MOTO')),
    marca       VARCHAR(40),
    color       VARCHAR(30),
    cliente_id  INTEGER     NOT NULL REFERENCES cliente (id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE mensualidad (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vehiculo_id   INTEGER       NOT NULL REFERENCES vehiculo (id) ON DELETE CASCADE,
    fecha_inicio  DATE          NOT NULL,
    fecha_fin     DATE          NOT NULL,
    valor         DECIMAL(12,2) NOT NULL CHECK (valor >= 0),
    CHECK (fecha_fin >= fecha_inicio)
);

CREATE TABLE celda (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo         VARCHAR(10) NOT NULL UNIQUE,
    tipo_vehiculo  VARCHAR(10) NOT NULL CHECK (tipo_vehiculo IN ('CARRO', 'MOTO')),
    estado         VARCHAR(15) NOT NULL DEFAULT 'LIBRE'
                   CHECK (estado IN ('LIBRE', 'OCUPADA', 'MANTENIMIENTO'))
);

CREATE TABLE registro_parqueo (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    vehiculo_id         INTEGER  NOT NULL REFERENCES vehiculo (id) ON DELETE RESTRICT,
    celda_id            INTEGER  NOT NULL REFERENCES celda (id)    ON DELETE RESTRICT,
    fecha_entrada       DATETIME NOT NULL,
    fecha_salida        DATETIME,
    usuario_entrada_id  INTEGER  NOT NULL REFERENCES usuario (id),
    usuario_salida_id   INTEGER  REFERENCES usuario (id),
    CHECK (fecha_salida IS NULL OR fecha_salida >= fecha_entrada)
);

CREATE UNIQUE INDEX ux_registro_vehiculo_abierto ON registro_parqueo (vehiculo_id) WHERE fecha_salida IS NULL;
CREATE UNIQUE INDEX ux_registro_celda_abierta    ON registro_parqueo (celda_id)    WHERE fecha_salida IS NULL;
CREATE INDEX ix_registro_fecha_entrada ON registro_parqueo (fecha_entrada);

CREATE TABLE novedad (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    registro_id  INTEGER      NOT NULL REFERENCES registro_parqueo (id) ON DELETE CASCADE,
    usuario_id   INTEGER      NOT NULL REFERENCES usuario (id),
    fecha        DATETIME     NOT NULL,
    tipo         VARCHAR(20)  NOT NULL CHECK (tipo IN ('DANO', 'OBJETO', 'INCIDENTE', 'OTRO')),
    descripcion  VARCHAR(500) NOT NULL
);
