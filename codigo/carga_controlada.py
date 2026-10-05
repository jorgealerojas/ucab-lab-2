"""Genera una carga pequeña y segura contra una Lambda Function URL.

No es una herramienta de benchmarking. Su propósito es producir suficientes
invocaciones para observar métricas y logs durante el laboratorio.
"""

import argparse
import json
import math
import statistics
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MAX_SOLICITUDES = 200
MAX_CONCURRENCIA = 10


def entero_en_rango(nombre, minimo, maximo):
    """Crea un validador de argparse para un entero dentro de un rango."""

    def validar(valor):
        try:
            numero = int(valor)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{nombre} debe ser un número entero.") from None
        if not minimo <= numero <= maximo:
            raise argparse.ArgumentTypeError(
                f"{nombre} debe estar entre {minimo} y {maximo}."
            )
        return numero

    return validar


def crear_parametros(numero):
    """Crea casos válidos y un 10 % de casos inválidos de manera reproducible."""
    if numero % 10 == 0:
        return {"producto": "teclado", "cantidad": "cero", "precio": "25.00"}, False

    productos = ("teclado", "ratón", "monitor", "audífonos")
    return {
        "producto": productos[numero % len(productos)],
        "cantidad": str((numero % 4) + 1),
        "precio": f"{15 + (numero % 30) + 0.50:.2f}",
    }, True


def invocar(url_base, numero, timeout):
    """Realiza una solicitud y devuelve datos simples para el resumen."""
    parametros, era_valida = crear_parametros(numero)
    separador = "&" if "?" in url_base else "?"
    url = f"{url_base}{separador}{urlencode(parametros)}"
    solicitud = Request(url, headers={"User-Agent": "UCAB-Laboratorio-Cloud/1.0"})
    inicio = time.perf_counter()

    try:
        with urlopen(solicitud, timeout=timeout) as respuesta:
            cuerpo = respuesta.read().decode("utf-8", errors="replace")
            status = respuesta.status
        error_red = None
    except HTTPError as error:
        # Un 400 esperado sigue siendo una respuesta válida del servicio.
        cuerpo = error.read().decode("utf-8", errors="replace")
        status = error.code
        error_red = None
    except (URLError, TimeoutError, OSError) as error:
        cuerpo = ""
        status = None
        error_red = type(error).__name__

    latencia_ms = (time.perf_counter() - inicio) * 1000
    json_valido = False
    if cuerpo:
        try:
            json.loads(cuerpo)
            json_valido = True
        except json.JSONDecodeError:
            pass

    return {
        "status": status,
        "latencia_ms": latencia_ms,
        "error_red": error_red,
        "json_valido": json_valido,
        "caso_valido": era_valida,
    }


def percentil_95(valores):
    """Calcula un percentil 95 sencillo sin dependencias externas."""
    ordenados = sorted(valores)
    posicion = max(0, math.ceil(0.95 * len(ordenados)) - 1)
    return ordenados[posicion]


def imprimir_resumen(resultados, duracion_total):
    """Muestra los resultados agregados, sin imprimir cada solicitud."""
    estados = Counter(
        str(resultado["status"]) if resultado["status"] is not None else "sin_respuesta"
        for resultado in resultados
    )
    errores_red = Counter(
        resultado["error_red"] for resultado in resultados if resultado["error_red"]
    )
    latencias = [resultado["latencia_ms"] for resultado in resultados]
    casos_invalidos = sum(not resultado["caso_valido"] for resultado in resultados)
    cuerpos_no_json = sum(
        resultado["status"] is not None and not resultado["json_valido"]
        for resultado in resultados
    )

    print("\nResumen de la carga controlada")
    print("=" * 31)
    print(f"Solicitudes completadas: {len(resultados)}")
    print(f"Casos inválidos intencionales: {casos_invalidos}")
    print(f"Duración total: {duracion_total:.2f} s")
    print("Estados HTTP: " + ", ".join(f"{estado}={total}" for estado, total in sorted(estados.items())))
    print(
        "Latencia (ms): "
        f"mín={min(latencias):.1f}, "
        f"promedio={statistics.fmean(latencias):.1f}, "
        f"mediana={statistics.median(latencias):.1f}, "
        f"p95={percentil_95(latencias):.1f}, "
        f"máx={max(latencias):.1f}"
    )
    print(f"Respuestas que no eran JSON: {cuerpos_no_json}")
    if errores_red:
        print("Errores de red: " + ", ".join(f"{tipo}={total}" for tipo, total in errores_red.items()))
    else:
        print("Errores de red: 0")


def analizar_argumentos():
    parser = argparse.ArgumentParser(
        description="Envía una carga pequeña a la Function URL del laboratorio."
    )
    parser.add_argument("url", help="URL HTTPS de la función Lambda")
    parser.add_argument(
        "--solicitudes",
        type=entero_en_rango("solicitudes", 1, MAX_SOLICITUDES),
        default=60,
        help=f"cantidad total (1-{MAX_SOLICITUDES}; predeterminado: 60)",
    )
    parser.add_argument(
        "--concurrencia",
        type=entero_en_rango("concurrencia", 1, MAX_CONCURRENCIA),
        default=5,
        help=f"solicitudes simultáneas (1-{MAX_CONCURRENCIA}; predeterminado: 5)",
    )
    parser.add_argument(
        "--timeout",
        type=entero_en_rango("timeout", 1, 30),
        default=10,
        help="espera máxima por solicitud en segundos (1-30; predeterminado: 10)",
    )
    return parser.parse_args()


def main():
    args = analizar_argumentos()
    if not args.url.lower().startswith("https://"):
        raise SystemExit("Error: la URL debe comenzar con https://")

    print(
        f"Iniciando {args.solicitudes} solicitudes con "
        f"concurrencia {args.concurrencia}."
    )
    print("Esta es una demostración controlada, no una prueba de estrés.")
    inicio = time.perf_counter()
    resultados = []

    with ThreadPoolExecutor(max_workers=args.concurrencia) as ejecutor:
        tareas = [
            ejecutor.submit(invocar, args.url, numero, args.timeout)
            for numero in range(1, args.solicitudes + 1)
        ]
        for tarea in as_completed(tareas):
            resultados.append(tarea.result())

    imprimir_resumen(resultados, time.perf_counter() - inicio)


if __name__ == "__main__":
    main()

