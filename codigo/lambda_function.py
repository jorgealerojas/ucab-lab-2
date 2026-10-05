"""Función Lambda para el laboratorio introductorio de computación en la nube.

La función recibe solicitudes GET desde una Lambda Function URL con estos
parámetros de consulta: producto, cantidad y precio.
"""

import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ENCABEZADOS_JSON = {
    "Content-Type": "application/json; charset=utf-8",
}


class ErrorDeEntrada(ValueError):
    """Error esperado cuando los datos enviados por el cliente no son válidos."""


def marca_de_tiempo_utc():
    """Devuelve la hora UTC en formato ISO 8601, por ejemplo ...Z."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def crear_respuesta(status_code, contenido):
    """Construye una respuesta compatible con Lambda Function URL."""
    return {
        "statusCode": status_code,
        "headers": ENCABEZADOS_JSON,
        "body": json.dumps(contenido, ensure_ascii=False),
    }


def obtener_request_id(context):
    """Obtiene el identificador asignado por Lambda, con apoyo para pruebas locales."""
    return getattr(context, "aws_request_id", "prueba-local")


def validar_parametros(parametros):
    """Valida los parámetros y devuelve valores listos para realizar el cálculo."""
    parametros = parametros or {}

    producto = str(parametros.get("producto", "")).strip()
    if not producto:
        raise ErrorDeEntrada("El parámetro 'producto' es obligatorio.")
    if len(producto) > 80:
        raise ErrorDeEntrada("El parámetro 'producto' admite como máximo 80 caracteres.")

    cantidad_texto = str(parametros.get("cantidad", "")).strip()
    try:
        cantidad = int(cantidad_texto)
    except (TypeError, ValueError):
        raise ErrorDeEntrada("El parámetro 'cantidad' debe ser un número entero.") from None
    if cantidad < 1 or cantidad > 1000:
        raise ErrorDeEntrada("El parámetro 'cantidad' debe estar entre 1 y 1000.")

    precio_texto = str(parametros.get("precio", "")).strip()
    try:
        precio = Decimal(precio_texto)
    except (InvalidOperation, ValueError):
        raise ErrorDeEntrada("El parámetro 'precio' debe ser un número válido.") from None
    if not precio.is_finite() or precio <= 0 or precio > Decimal("1000000"):
        raise ErrorDeEntrada("El parámetro 'precio' debe ser mayor que 0 y menor o igual a 1000000.")

    precio = precio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    subtotal = (precio * cantidad).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return producto, cantidad, precio, subtotal


def lambda_handler(event, context):
    """Punto de entrada que AWS Lambda invoca para cada solicitud."""
    request_id = obtener_request_id(context)
    region = os.environ.get("AWS_REGION", "desconocida")
    timestamp_utc = marca_de_tiempo_utc()

    try:
        metodo = (
            (event or {}).get("requestContext", {})
            .get("http", {})
            .get("method", "GET")
            .upper()
        )
        if metodo != "GET":
            logger.warning("Solicitud rechazada request_id=%s causa=metodo_no_permitido", request_id)
            return crear_respuesta(
                405,
                {
                    "estado": "error",
                    "mensaje": "Método no permitido. Utilice GET.",
                    "request_id": request_id,
                    "region": region,
                    "timestamp_utc": timestamp_utc,
                },
            )

        producto, cantidad, precio, subtotal = validar_parametros(
            (event or {}).get("queryStringParameters")
        )

        # No se registra el producto ni el evento completo para evitar exponer datos.
        logger.info(
            "Solicitud procesada request_id=%s estado=procesado cantidad=%d",
            request_id,
            cantidad,
        )
        return crear_respuesta(
            200,
            {
                "producto": producto,
                "cantidad": cantidad,
                "precio_unitario": float(precio),
                "subtotal": float(subtotal),
                "estado": "procesado",
                "request_id": request_id,
                "region": region,
                "timestamp_utc": timestamp_utc,
            },
        )

    except ErrorDeEntrada as error:
        logger.warning("Solicitud inválida request_id=%s causa=validacion", request_id)
        return crear_respuesta(
            400,
            {
                "estado": "error",
                "mensaje": str(error),
                "request_id": request_id,
                "region": region,
                "timestamp_utc": timestamp_utc,
            },
        )
    except Exception:
        # El detalle técnico queda en CloudWatch, pero no se expone al cliente.
        logger.exception("Error inesperado request_id=%s", request_id)
        return crear_respuesta(
            500,
            {
                "estado": "error",
                "mensaje": "Ocurrió un error interno. Intente nuevamente.",
                "request_id": request_id,
                "region": region,
                "timestamp_utc": timestamp_utc,
            },
        )

