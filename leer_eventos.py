import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo
from icalendar import Calendar  

# ---------- CONFIGURACIÓN ----------
ASIGNATURAS = {
    "2059001": "Lógica",
    "2059002": "Álgebra Lineal y Mat. Discreta",
    "2059003": "Fund. Físicos de la Informática",
    "2059004": "Introducción a la Programación",
    "2059006": "Cálculo",
    "2059007": "Principios Jurídicos y Deontología",
    "2059008": "Estructuras de Datos",
    "2059009": "Fundamentos de Computadores",
    "2059010": "Informática y Sociedad",
    "2059011": "Estadística",
}
IGNORAR = ("COM", "ESCO")
ZONA = ZoneInfo("Europe/Madrid")


# ---------- FUNCIÓN ----------
def nombre_asignatura(codigo):
    """Devuelve el nombre de la asignatura, 'RAC', o None si hay que ignorarlo."""
    if codigo.startswith(IGNORAR):
        return None
    if codigo.startswith("RAC"):
        return "RAC"
    partes = codigo.split("_")
    if len(partes) >= 2 and partes[1] in ASIGNATURAS:
        return ASIGNATURAS[partes[1]]
    return "DESCONOCIDA (" + codigo + ")"

def urgencia(dias, titulo):
    """Devuelve una etiqueta de urgencia según los días que faltan."""
    if "No evaluable" in titulo:
        return "⚪ Baja"
    if dias <= 2:
        return "🔴 Urgente"
    elif dias <= 7:
        return "🟠 Esta semana"
    elif dias <= 14:
        return "🟡 Próximas 2 semanas"
    else:
        return "🟢 Con calma"


# ---------- PROGRAMA PRINCIPAL ----------
with open("enlace.txt") as archivo:
    url = archivo.read().strip()

respuesta = requests.get(url)
calendario = Calendar.from_ical(respuesta.content)
ahora = datetime.now(ZONA)

tareas = []
for evento in calendario.walk("VEVENT"):
    titulo = str(evento.get("SUMMARY"))

    cat = evento.get("CATEGORIES")
    codigo = "SIN_CATEGORIA" if cat is None else cat.to_ical().decode()

    asignatura = nombre_asignatura(codigo)
    if asignatura is None:
        continue

    fecha = evento.get("DTSTART").dt
    if not isinstance(fecha, datetime):
        fecha = datetime.combine(fecha, time(23, 59), ZONA)
    fecha = fecha.astimezone(ZONA)

    if fecha < ahora:
        continue

    tareas.append((fecha, asignatura, titulo))

tareas.sort()

for fecha, asignatura, titulo in tareas:
    dias = (fecha - ahora).days
    nivel = urgencia(dias, titulo)
    print(f"{nivel} | {fecha:%d/%m %H:%M} | {asignatura} - {titulo}")