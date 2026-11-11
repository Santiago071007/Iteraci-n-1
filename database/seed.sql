INSERT INTO cliente (documento, nombres, telefono, email) VALUES
    ('1020304050', 'Laura Gómez Rincón',   '3104567890', 'laura.gomez@correo.com'),
    ('79876543',   'Carlos Pérez Duarte',  '3209876543', 'carlos.perez@correo.com'),
    ('52123456',   'Marta Lucía Ospina',   '3001234567', 'marta.ospina@correo.com'),
    ('1012345678', 'Andrés Felipe Rojas',  '3157654321', 'andres.rojas@correo.com');

INSERT INTO vehiculo (placa, tipo, marca, color, cliente_id) VALUES
    ('ABC123', 'CARRO', 'Mazda',     'Rojo',   1),
    ('JKL456', 'CARRO', 'Renault',   'Gris',   2),
    ('XYZ78D', 'MOTO',  'Yamaha',    'Negro',  3),
    ('MNO901', 'CARRO', 'Chevrolet', 'Blanco', 4),
    ('QRS234', 'CARRO', 'Kia',       'Azul',   2);

INSERT INTO mensualidad (vehiculo_id, fecha_inicio, fecha_fin, valor) VALUES
    (1, date('now', 'localtime', '-10 days'), date('now', 'localtime', '+20 days'), 180000),
    (2, date('now', 'localtime', '-5 days'),  date('now', 'localtime', '+25 days'), 180000),
    (3, date('now', 'localtime', '-2 days'),  date('now', 'localtime', '+28 days'),  90000),
    (4, date('now', 'localtime', '-15 days'), date('now', 'localtime', '+15 days'), 180000),
    (5, date('now', 'localtime', '-60 days'), date('now', 'localtime', '-30 days'), 180000);

INSERT INTO celda (codigo, tipo_vehiculo, estado) VALUES
    ('A-01', 'CARRO', 'LIBRE'), ('A-02', 'CARRO', 'LIBRE'), ('A-03', 'CARRO', 'LIBRE'),
    ('A-04', 'CARRO', 'LIBRE'), ('A-05', 'CARRO', 'LIBRE'), ('A-06', 'CARRO', 'LIBRE'),
    ('A-07', 'CARRO', 'LIBRE'), ('A-08', 'CARRO', 'MANTENIMIENTO'),
    ('M-01', 'MOTO',  'LIBRE'), ('M-02', 'MOTO',  'LIBRE'), ('M-03', 'MOTO',  'LIBRE'),
    ('M-04', 'MOTO',  'LIBRE');
