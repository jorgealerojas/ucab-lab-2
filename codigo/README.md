# Código del laboratorio: AWS Lambda, Function URL y CloudWatch

Estos archivos acompañan el laboratorio introductorio de la Unidad II. Todo el
código utiliza únicamente la biblioteca estándar de Python; no es necesario
instalar paquetes con `pip`.

## Archivos

- `lambda_function.py`: función que se copia al editor de código de AWS Lambda.
- `carga_controlada.py`: programa local que envía una carga pequeña al endpoint.

## 1. Configurar la función Lambda

1. Cree una función Lambda con un runtime de Python disponible en la consola.
2. Mantenga el nombre del archivo `lambda_function.py` y el handler
   `lambda_function.lambda_handler`.
3. Copie el contenido de `lambda_function.py` en el editor de código de Lambda.
4. Presione **Deploy**.
5. Use 128 MB de memoria y un timeout de 3 segundos para el laboratorio.

La función espera una solicitud `GET` con tres parámetros:

| Parámetro | Ejemplo | Regla |
|---|---:|---|
| `producto` | `teclado` | Obligatorio; máximo 80 caracteres |
| `cantidad` | `3` | Entero entre 1 y 1000 |
| `precio` | `25.50` | Número mayor que 0 y máximo 1000000 |

### Evento de prueba correcto en la consola

```json
{
  "requestContext": {
    "http": {
      "method": "GET"
    }
  },
  "queryStringParameters": {
    "producto": "teclado",
    "cantidad": "3",
    "precio": "25.50"
  }
}
```

La respuesta debe tener `statusCode` 200. El campo `body` contiene un texto JSON
parecido a este:

```json
{
  "producto": "teclado",
  "cantidad": 3,
  "precio_unitario": 25.5,
  "subtotal": 76.5,
  "estado": "procesado",
  "request_id": "...",
  "region": "...",
  "timestamp_utc": "..."
}
```

### Evento de prueba inválido

Cambie `"cantidad": "3"` por `"cantidad": "cero"`. La función debe responder
con `statusCode` 400 y un mensaje de validación. Este error controlado no debe
confundirse con una falla interna de la plataforma.

## 2. Crear y probar la Function URL

Cree una Function URL temporal con tipo de autenticación `NONE`, solamente según
las instrucciones del laboratorio. No use datos personales o sensibles. Después
de desplegarla, pruebe en el navegador sustituyendo `SU-FUNCTION-URL`:

```text
https://SU-FUNCTION-URL/?producto=teclado&cantidad=3&precio=25.50
```

La URL es pública mientras exista. No la publique en redes sociales ni la
incluya en un repositorio público y elimínela al terminar la práctica.

## 3. Ejecutar la carga controlada

En una terminal, ubíquese en esta carpeta y ejecute:

```bash
python3 carga_controlada.py "https://SU-FUNCTION-URL/"
```

En Windows también puede ser necesario usar `python` en lugar de `python3`:

```powershell
python carga_controlada.py "https://SU-FUNCTION-URL/"
```

La ejecución predeterminada realiza 60 solicitudes con concurrencia 5. El 10 %
son entradas inválidas intencionales, por lo que es normal observar respuestas
HTTP 400 junto con respuestas 200.

Puede hacer una prueba inicial más pequeña:

```bash
python3 carga_controlada.py "https://SU-FUNCTION-URL/" --solicitudes 10 --concurrencia 2
```

El programa limita intencionalmente la ejecución a 200 solicitudes y 10 tareas
simultáneas. No elimine esos límites ni repita la carga innecesariamente. Esta
actividad genera datos para CloudWatch; no pretende medir el rendimiento máximo
de AWS Lambda.

## 4. Interpretar el resumen y CloudWatch

El resumen local muestra:

- cantidad de respuestas por estado HTTP;
- latencia mínima, promedio, mediana, percentil 95 y máxima;
- respuestas que no contenían JSON;
- errores de red o timeout.

En CloudWatch, compare el resumen con las métricas **Invocations**, **Errors** y
**Duration**, y revise el grupo de logs `/aws/lambda/NOMBRE-DE-LA-FUNCION`.
Recuerde: una respuesta HTTP 400 construida por nuestro código es una invocación
completada, y no necesariamente aumenta la métrica `Errors` de Lambda.

## 5. Limpieza

Al finalizar:

1. Elimine la Function URL pública.
2. Elimine la función Lambda siguiendo la guía del laboratorio.
3. Si el docente lo solicita, elimine el grupo de logs de CloudWatch y el rol de
   ejecución creado para la práctica.

No deje una URL pública activa después de la sesión.
