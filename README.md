# Laboratorio Unidad II — Fundamentos de computación en la nube

Laboratorio introductorio de AWS para estudiantes de Ingeniería Informática. Durante una sesión de 1 hora y 45 minutos, cada estudiante despliega un servicio serverless, lo publica temporalmente mediante HTTPS y examina sus logs y métricas.

## Servicios utilizados

- AWS Lambda
- Lambda Function URL
- AWS Identity and Access Management (IAM)
- Amazon CloudWatch

## Contenido

- [`guia_estudiantes.md`](guia_estudiantes.md): instrucciones completas del laboratorio, evidencias, análisis y limpieza.
- [`codigo/lambda_function.py`](codigo/lambda_function.py): función que se despliega en AWS Lambda.
- [`codigo/carga_controlada.py`](codigo/carga_controlada.py): script local de carga pequeña y limitada.
- [`codigo/README.md`](codigo/README.md): referencia rápida para utilizar los programas.

## Configuración del laboratorio

- Región: `us-east-2`.
- Nombre de la función: `ucab-flash-sale-<iniciales>`.
- Runtime: una versión disponible y mantenida de Python.
- Memoria: 128 MB.
- Timeout: 3 segundos.
- Function URL: pública con `AuthType: NONE` solamente durante la práctica.
- Carga indicada: 50 solicitudes con concurrencia 5.

El script de carga utiliza solamente la biblioteca estándar de Python y detecta
automáticamente las ubicaciones habituales del almacén CA, incluida la ruta de
Ubuntu y Debian.

## Inicio

1. Descarga o clona este repositorio.
2. Abre [`guia_estudiantes.md`](guia_estudiantes.md).
3. Sigue la guía en orden y usa los archivos de la carpeta [`codigo`](codigo/).
4. Antes de finalizar, elimina la Function URL, la función Lambda y el grupo de logs creado para la práctica.

La práctica emplea datos ficticios. No publiques la Function URL, credenciales ni información personal.
