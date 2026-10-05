# Laboratorio de la Unidad II: mi primer servicio serverless en AWS

**Asignatura:** Fundamentos de Computación en la Nube  
**Duración:** 1 h 45 min  
**Modalidad:** individual  
**Servicios:** AWS Lambda, Lambda Function URL, AWS Identity and Access Management (IAM) y Amazon CloudWatch  
**Región obligatoria:** `us-east-1` (N. Virginia)

> Los nombres y la ubicación exacta de algunas opciones pueden variar ligeramente entre las versiones en español e inglés de la consola. No cambies de región durante el laboratorio.

## 1. Situación

Una tienda necesita publicar rápidamente un servicio para procesar solicitudes durante una venta especial. El servicio recibirá el nombre de un producto, su cantidad y precio unitario; validará esos datos y devolverá el subtotal. También generará información de observabilidad para comprender dónde y cómo se ejecutó.

En lugar de aprovisionar una máquina virtual, instalar un sistema operativo y mantener un servidor web, desplegarás el código como una función administrada por AWS.

La arquitectura será:

```text
Navegador o script ──HTTPS──> Lambda Function URL ──> AWS Lambda
                                                        │
                                                        └──> CloudWatch Logs y métricas
                                IAM ──permisos──> rol de ejecución
```

## 2. Objetivos de aprendizaje

Al finalizar podrás:

1. Aprovisionar un recurso cloud mediante autoservicio.
2. Desplegar código sin administrar un servidor.
3. Invocar una función mediante un endpoint HTTPS temporal.
4. Consultar logs y métricas de ejecución.
5. Diferenciar las responsabilidades de AWS y las del desarrollador.
6. Relacionar la experiencia con las cinco características esenciales de cloud definidas por NIST.
7. Comparar, a nivel introductorio, una función serverless con una aplicación alojada en una máquina virtual.

## 3. Prerrequisitos

Antes de comenzar, confirma que tienes:

- Una cuenta individual de AWS en el **Free Plan** y acceso a la consola.
- Un navegador actualizado.
- Python 3 instalado en tu equipo para la prueba de carga. Compruébalo con `python3 --version` en Linux/macOS o `py --version` en Windows.
- Los archivos entregados por el docente:
  - `codigo/lambda_function.py`
  - `codigo/carga_controlada.py`
- Un editor de texto.

No necesitas instalar AWS CLI, crear una VPC ni usar una tarjeta de crédito para esta práctica.

## 4. Reglas de costo, alcance y seguridad

Cumple estas reglas durante toda la sesión:

- Trabaja únicamente en `us-east-1`.
- Crea **una sola función**, con **128 MB** de memoria y **3 segundos** de timeout.
- Ejecuta como máximo **100 solicitudes** con el script de carga.
- No actives Lambda Insights, X-Ray, Live Tail, alarmas, dashboards personalizados, provisioned concurrency ni otros servicios.
- No uses API Gateway, EC2, RDS, NAT Gateway, balanceadores ni bases de datos.
- La Function URL usará temporalmente `AuthType: NONE`. Esto significa que será pública. No compartas la URL, no proceses datos reales y elimínala al finalizar.
- No coloques contraseñas, credenciales, tokens, correos personales ni otros datos sensibles en el código, parámetros o logs.
- No actives funciones avanzadas del plan ni conviertas la cuenta a un plan pago.
- Si la consola te pide agregar un método de pago, cambiar de plan, comprar una suscripción o crear un recurso distinto, **detente y consulta al docente**.

Aunque el consumo previsto es mínimo, “Free Plan” no significa que cualquier recurso o volumen de uso sea ilimitado. El control principal de este laboratorio es el alcance anterior y la eliminación final de los recursos.

## 5. Cronograma de trabajo

| Minutos | Actividad |
|---:|---|
| 0–10 | Verificar cuenta, plan y región |
| 10–25 | Crear y configurar la función |
| 25–45 | Pegar el código, desplegarlo y probar desde la consola |
| 45–60 | Crear y probar la Function URL |
| 60–75 | Ejecutar pruebas funcionales y carga controlada |
| 75–90 | Examinar logs y métricas |
| 90–98 | Analizar arquitectura y características NIST |
| 98–105 | Guardar evidencias y eliminar recursos |

## 6. Parte A — Verificar la cuenta y la región

1. Inicia sesión en la consola de AWS con tu cuenta individual.
2. Comprueba en la sección de facturación o información de la cuenta que permaneces en el **Free Plan**. No selecciones ninguna opción para pasar a un plan pago.
3. En el selector de región de la barra superior, elige **US East (N. Virginia) `us-east-1`**.
4. Anota tus iniciales en minúsculas, sin espacios ni acentos. Ejemplo: Ana Pérez Gómez usaría `apg`.
5. Define el nombre que emplearás en toda la práctica:

   ```text
   ucab-flash-sale-<iniciales>
   ```

   Ejemplo: `ucab-flash-sale-apg`.

> Si dos estudiantes comparten accidentalmente una cuenta, agreguen un número corto al final. La modalidad esperada es una cuenta por estudiante.

## 7. Parte B — Crear la función Lambda

1. En el buscador superior de servicios escribe **Lambda** y abre el servicio.
2. Confirma nuevamente que la región superior sea `us-east-1`.
3. Abre **Functions / Funciones** y selecciona **Create function / Crear función**.
4. Selecciona **Author from scratch / Crear desde cero**.
5. Completa la información básica:
   - **Function name / Nombre:** `ucab-flash-sale-<iniciales>`.
   - **Runtime / Entorno de ejecución:** la versión de **Python** disponible que indique el docente. Usa una versión mantenida; no cambies luego a Node.js u otro lenguaje.
   - **Architecture / Arquitectura:** `x86_64`.
6. En permisos, conserva **Create a new role with basic Lambda permissions / Crear un rol nuevo con permisos básicos de Lambda**.
7. No habilites Function URL todavía y no cambies las demás opciones avanzadas.
8. Selecciona **Create function / Crear función** y espera el mensaje de creación exitosa.

### ¿Qué ocurrió?

AWS creó la función y un rol de ejecución de IAM. Ese rol permite, entre otras acciones básicas, escribir los logs de la función en CloudWatch. No concede acceso general a todos los servicios.

### Configurar memoria y timeout

1. Dentro de la función, abre **Configuration / Configuración**.
2. En **General configuration / Configuración general**, selecciona **Edit / Editar**.
3. Establece:
   - **Memory / Memoria:** `128 MB`.
   - **Timeout:** `0 min 3 sec`.
4. Guarda los cambios.
5. Comprueba que no esté activada la concurrencia aprovisionada (*provisioned concurrency*).

## 8. Parte C — Instalar y desplegar el código

1. Regresa a la pestaña **Code / Código**.
2. En el editor integrado, abre `lambda_function.py`.
3. En tu equipo, abre el archivo entregado `codigo/lambda_function.py`.
4. Copia **todo** su contenido.
5. Reemplaza por completo el contenido del archivo del mismo nombre en la consola de Lambda.
6. Selecciona **Deploy / Implementar**. Guardar el texto en el editor no basta: debes desplegarlo.
7. Espera la confirmación de que los cambios fueron implementados.

No renombres `lambda_function.py` ni la función `lambda_handler`, pues el handler predeterminado espera `lambda_function.lambda_handler`.

## 9. Parte D — Primera prueba desde la consola

Esta prueba invoca Lambda desde el plano de control de AWS, sin publicar todavía un endpoint.

1. En la sección de código, selecciona **Test / Probar** y crea un evento nuevo.
2. Asígnale el nombre `pedido-valido`.
3. Reemplaza el JSON de ejemplo con este evento, equivalente a un `GET` válido recibido por la Function URL:

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
       "precio": "25"
     }
   }
   ```
4. Guarda el evento y ejecútalo.
5. Comprueba en el resultado:
   - Estado de ejecución exitoso.
   - Código HTTP `200` dentro de la respuesta devuelta por el handler.
   - Producto, cantidad, precio unitario y subtotal correctos.
   - Un identificador de solicitud y una marca de tiempo.
6. Copia el `RequestId` mostrado por Lambda: luego lo buscarás en CloudWatch.

Ahora crea un segundo evento llamado `pedido-invalido` con este contenido y ejecútalo:

```json
{
  "requestContext": {
    "http": {
      "method": "GET"
    }
  },
  "queryStringParameters": {
    "producto": "teclado",
    "cantidad": "0",
    "precio": "25"
  }
}
```

Debe producir una respuesta controlada con `statusCode` igual a `400`, pues la cantidad debe ser un entero mayor que cero.

> Una respuesta HTTP controlada `400` no necesariamente incrementa la métrica **Errors** de Lambda. Para Lambda, el código terminó correctamente si el handler capturó el problema y devolvió una respuesta. La métrica **Errors** registra, entre otros casos, excepciones no controladas y fallas del runtime.

## 10. Parte E — Crear una Function URL temporal

La URL será pública solamente durante el laboratorio.

1. Abre **Configuration / Configuración** dentro de la función.
2. Selecciona **Function URL**.
3. Selecciona **Create function URL / Crear URL de función**.
4. En **Auth type / Tipo de autenticación**, elige `NONE`.
5. Lee y acepta el aviso que confirma que cualquier persona con la URL podrá invocar la función.
6. Si aparece **Invoke mode / Modo de invocación**, conserva `BUFFERED`.
7. No configures CORS para esta práctica; las invocaciones serán desde la barra del navegador o desde Python, no desde código JavaScript ejecutado en otra página web.
8. Guarda la configuración.
9. Copia la URL generada en un archivo temporal de notas. Debe parecerse a:

   ```text
   https://<identificador>.lambda-url.us-east-1.on.aws/
   ```

**No incluyas la URL completa en una entrega pública.** Puedes mostrarla parcialmente oculta en una captura, si el docente solicita evidencia visual.

## 11. Parte F — Pruebas funcionales por HTTPS

### Prueba válida

En la barra del navegador, agrega los parámetros a tu Function URL:

```text
https://<tu-url>.lambda-url.us-east-1.on.aws/?producto=teclado&cantidad=3&precio=25
```

Comprueba que:

- La respuesta sea JSON.
- El producto sea `teclado`.
- La cantidad sea `3`.
- El precio unitario sea `25`.
- El subtotal sea `75`.
- La región informada sea `us-east-1`.

### Pruebas inválidas

Ejecuta al menos dos de estas variantes:

```text
?producto=teclado&cantidad=abc&precio=25
?producto=teclado&cantidad=-2&precio=25
?cantidad=3&precio=25
?producto=teclado&cantidad=3&precio=0
```

Registra para cada una el código o mensaje de error y explica qué validación falló.

### Pregunta breve

¿Por qué el navegador puede invocar el servicio sin iniciar sesión en AWS? Relaciona tu respuesta con `AuthType: NONE` y con el acceso por red.

## 12. Parte G — Carga controlada

La finalidad no es medir el límite de AWS ni realizar una prueba profesional de rendimiento. Solo se generarán suficientes invocaciones para observar medición y concurrencia básica.

1. Abre una terminal en la carpeta que contiene `codigo/carga_controlada.py`.
2. Consulta la ayuda del programa:

   ```bash
   python3 codigo/carga_controlada.py --help
   ```

   En Windows puedes sustituir `python3` por `py`.
3. Ejecuta el siguiente comando, sustituyendo la URL de ejemplo por tu Function URL. Conserva las comillas:

   ```bash
   python3 codigo/carga_controlada.py "https://<tu-url>.lambda-url.us-east-1.on.aws/" --solicitudes 50 --concurrencia 5
   ```

   En Windows:

   ```powershell
   py codigo/carga_controlada.py "https://<tu-url>.lambda-url.us-east-1.on.aws/" --solicitudes 50 --concurrencia 5
   ```

   El programa intercala algunos casos inválidos para verificar las respuestas `400`; no superes 100 solicitudes ni aumentes la concurrencia indicada.
4. Conserva el resumen final que muestre el script: solicitudes exitosas, fallidas y duración aproximada.
5. Si todas fallan, detén la prueba; no aumentes el número de solicitudes. Revisa primero la URL y una invocación manual.

> No instales herramientas de carga adicionales. El script provisto usa la biblioteca estándar de Python y limita la concurrencia.

## 13. Parte H — Explorar CloudWatch

Los datos pueden tardar algunos minutos en aparecer. Aprovecha ese intervalo para completar las preguntas conceptuales.

### Ver logs

1. Regresa a tu función Lambda y abre **Monitor / Supervisar**.
2. Selecciona **View CloudWatch logs / Ver logs de CloudWatch**. No abras **Live Tail**, pues no es necesario para el laboratorio y puede tener costo por tiempo de sesión.
3. Abre el grupo de logs:

   ```text
   /aws/lambda/ucab-flash-sale-<iniciales>
   ```

4. Abre el flujo de logs más reciente.
5. Localiza:
   - Las líneas `START`, `END` y `REPORT`.
   - El `RequestId` que guardaste.
   - Los mensajes generados por el código.
   - `Duration`, `Billed Duration`, `Memory Size` y `Max Memory Used`.
6. Registra una observación: ¿la memoria máxima usada fue menor, igual o mayor que los 128 MB configurados?

No concluyas que cada *log stream* es un servidor físico. Un flujo se asocia a un entorno de ejecución; AWS abstrae la infraestructura física.

### Ver métricas

1. Vuelve a **Lambda > tu función > Monitor**.
2. Examina como mínimo:
   - **Invocations / Invocaciones**.
   - **Errors / Errores**.
   - **Duration / Duración**.
3. Ajusta el intervalo al periodo de la práctica, si es necesario.
4. Espera entre 2 y 5 minutos y actualiza si los datos todavía no aparecen.
5. Registra:
   - Invocaciones aproximadas observadas.
   - Número de errores de Lambda.
   - Duración aproximada o rango de duración.
   - Diferencia entre “solicitud HTTP inválida” y “error de ejecución de Lambda”.

No se espera que el gráfico coincida exactamente con 50: también realizaste invocaciones desde la consola y el navegador, y las métricas se agregan por periodos.

## 14. Parte I — Análisis de fundamentos de cloud

Completa la tabla con una evidencia concreta de tu práctica. En “limitación”, indica qué no pudiste observar o demostrar directamente.

| Característica esencial NIST | Evidencia en el laboratorio | Limitación de la evidencia |
|---|---|---|
| Autoservicio bajo demanda |  |  |
| Acceso amplio por red |  |  |
| Pool común de recursos |  |  |
| Elasticidad rápida |  |  |
| Servicio medido |  |  |

Responde además, con dos o tres oraciones por pregunta:

1. ¿Qué componentes pertenecen al plano de control y cuáles al plano de ejecución?
2. ¿Qué administra AWS y qué administraste tú?
3. ¿Por qué esta solución se considera serverless aunque sí existan servidores físicos?
4. ¿Qué tendrías que instalar, configurar y mantener si desplegaras la misma lógica en una instancia EC2?
5. ¿La ráfaga de 50 solicitudes demuestra por sí sola elasticidad ilimitada? Justifica.
6. ¿Qué riesgo introdujo `AuthType: NONE` y cómo se reduciría en un sistema real?

## 15. Entregables

Entrega un único informe breve con:

1. Tu nombre, iniciales usadas y nombre de la función.
2. El código final de `lambda_function.py` o un enlace al repositorio indicado por el docente.
3. Resultado de una solicitud válida con subtotal correcto.
4. Resultados de dos solicitudes inválidas y explicación de sus validaciones.
5. Resumen de la carga controlada.
6. Evidencia de CloudWatch Logs donde se vean `RequestId`, `Duration` y uso de memoria. Oculta identificadores sensibles innecesarios.
7. Datos o gráfico de las métricas Invocations, Errors y Duration.
8. Diagrama de arquitectura sencillo, con cliente, Function URL, Lambda, IAM y CloudWatch.
9. Tabla NIST completa y respuestas de análisis.
10. Confirmación escrita de que eliminaste la Function URL, la función y el grupo de logs.

No publiques la Function URL ni credenciales en el informe.

## 16. Limpieza obligatoria

Realiza esta sección antes de cerrar la sesión, incluso si no terminaste las preguntas.

### 16.1 Eliminar primero la URL pública

1. Abre **Lambda > Functions > `ucab-flash-sale-<iniciales>`**.
2. Abre **Configuration > Function URL**.
3. Selecciona **Delete / Eliminar** y confirma.
4. Prueba la URL una vez más: ya no debe responder como antes.

### 16.2 Eliminar la función

1. Vuelve a la página de la función.
2. Selecciona **Actions / Acciones > Delete function / Eliminar función**.
3. Escribe la confirmación solicitada por AWS y elimina la función.

### 16.3 Eliminar el grupo de logs

Eliminar la función no necesariamente elimina sus logs existentes.

1. Abre **CloudWatch > Logs > Log groups / Grupos de logs**.
2. Busca `/aws/lambda/ucab-flash-sale-<iniciales>`.
3. Selecciona exclusivamente ese grupo.
4. Elige **Actions > Delete log group(s) / Eliminar grupos de logs** y confirma.

### 16.4 Rol de IAM

Si el docente lo indica, elimina también el rol creado automáticamente:

1. Abre **IAM > Roles**.
2. Busca el rol cuyo nombre comienza con `ucab-flash-sale-<iniciales>-role-`.
3. Abre el rol y confirma en **Last activity / Última actividad** y en sus relaciones que corresponde a tu función eliminada.
4. Elimina únicamente ese rol.

No elimines roles que no puedas asociar inequívocamente con esta práctica.

## 17. Solución de problemas

| Problema | Causa probable | Acción |
|---|---|---|
| No aparece la opción Function URL | Región incorrecta o vista equivocada | Confirma `us-east-1` y abre la pestaña **Configuration** de la función |
| La consola muestra el código anterior | El cambio no fue desplegado | Selecciona **Deploy** y vuelve a invocar |
| `Internal Server Error` | Excepción no controlada o formato de evento inesperado | Revisa el flujo más reciente de CloudWatch y compara el evento con los ejemplos del archivo |
| Respuesta de validación en todas las pruebas | Parámetros ausentes, nombres distintos o URL mal formada | Usa exactamente `producto`, `cantidad` y `precio`; conserva `?` y `&` |
| `AccessDenied` al crear o invocar | Permiso o política de cuenta insuficiente | No amplíes permisos por tu cuenta; muestra el mensaje al docente |
| No hay logs | La función aún no fue invocada, hay retraso o el rol no tiene permisos básicos | Ejecuta una prueba válida, espera unos minutos y confirma el rol básico |
| Las métricas aparecen vacías | Periodo o intervalo incorrecto, o retraso de publicación | Selecciona el intervalo de la clase, espera 2–5 minutos y actualiza |
| El script no reconoce `python3` | En Windows el lanzador suele ser `py` | Ejecuta `py codigo/carga_controlada.py --help` |
| Muchas solicitudes fallan | URL eliminada, error de código o conectividad | Detén la carga, prueba una sola solicitud en el navegador y consulta logs |
| El subtotal es incorrecto | Conversión numérica o versión no desplegada | Revisa los tipos, vuelve a desplegar y repite la prueba válida |

## 18. Cierre

Antes de entregar, verifica:

- [ ] Guardé las evidencias requeridas.
- [ ] No revelé credenciales ni la URL completa.
- [ ] Eliminé la Function URL pública.
- [ ] Eliminé la función Lambda.
- [ ] Eliminé su grupo de logs.
- [ ] Eliminé el rol solo si pude identificarlo con certeza y el docente lo indicó.
- [ ] Mi cuenta continúa en el Free Plan.

## Referencias oficiales de consulta

- [Crear una primera función Lambda](https://docs.aws.amazon.com/lambda/latest/dg/getting-started.html)
- [Crear y administrar Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html)
- [Invocar una Function URL](https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html)
- [Consultar logs de funciones Lambda](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html)
