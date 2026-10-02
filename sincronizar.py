import hashlib
import os.path
import requests
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from icalendar import Calendar
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# Trabajar siempre desde la carpeta donde está este archivo
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
PERMISOS = ["https://www.googleapis.com/auth/calendar"]
NOMBRE_CALENDARIO = "Uni - Tareas"

# NUEVO: color de Google Calendar para cada nivel de urgencia
COLORES = {
    "⚪ Baja": "8",              # grafito
    "🔴 Urgente": "11",          # tomate
    "🟠 Esta semana": "6",       # mandarina
    "🟡 Próximas 2 semanas": "5",  # plátano
    "🟢 Con calma": "10",        # albahaca
}


# ---------- FUNCIONES ----------
def nombre_asignatura(codigo):  # (ya la conoces)
    if codigo.startswith(IGNORAR):
        return None
    if codigo.startswith("RAC"):
        return "RAC"
    partes = codigo.split("_")
    if len(partes) >= 2 and partes[1] in ASIGNATURAS:
        return ASIGNATURAS[partes[1]]
    return "DESCONOCIDA (" + codigo + ")"


def urgencia(dias, titulo):  # (ya la conoces)
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


def conectar():  # (ya la conoces)
    credenciales = None
    if os.path.exists("token.json"):
        credenciales = Credentials.from_authorized_user_file("token.json", PERMISOS)
    if not credenciales or not credenciales.valid:
        if credenciales and credenciales.expired and credenciales.refresh_token:
            credenciales.refresh(Request())
        else:
            flujo = InstalledAppFlow.from_client_secrets_file("credentials.json", PERMISOS)
            credenciales = flujo.run_local_server(port=0)
        with open("token.json", "w") as archivo:
            archivo.write(credenciales.to_json())
    return build("calendar", "v3", credentials=credenciales)


def buscar_calendario(servicio, nombre):  # (ya la conoces)
    lista = servicio.calendarList().list().execute()
    nombres = []
    for cal in lista["items"]:
        nombres.append(cal["summary"])
        if cal["summary"] == nombre:
            return cal["id"]
    print("No encuentro ese calendario. Los que veo son:", nombres)
    return None


# NUEVO
def leer_tareas():
    """Lee el calendario de Moodle y devuelve las tareas futuras."""
    with open("enlace.txt") as archivo:
        url = archivo.read().strip()

    respuesta = requests.get(url, timeout=30)
    calendario = Calendar.from_ical(respuesta.content)
    ahora = datetime.now(ZONA)

    tareas = []
    for evento in calendario.walk("VEVENT"):
        titulo = str(evento.get("SUMMARY"))
        uid = str(evento.get("UID"))

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

        tareas.append((uid, fecha, asignatura, titulo))

    tareas.sort(key=lambda t: t[1])
    return tareas


# NUEVO
def crear_id(uid):
    """Convierte el UID de Moodle en un ID válido para Google (siempre el mismo)."""
    return hashlib.md5(uid.encode()).hexdigest()


# NUEVO
def guardar_evento(servicio, id_calendario, id_evento, cuerpo):
    """Actualiza el evento si existe; si no existe, lo crea."""
    try:
        servicio.events().update(
            calendarId=id_calendario, eventId=id_evento, body=cuerpo
        ).execute()
        return "actualizado"
    except HttpError as error:
        if error.resp.status == 404:
            cuerpo["id"] = id_evento
            servicio.events().insert(calendarId=id_calendario, body=cuerpo).execute()
            return "creado"
        raise


# ---------- PROGRAMA PRINCIPAL ----------
servicio = conectar()
id_calendario = buscar_calendario(servicio, NOMBRE_CALENDARIO)

if id_calendario is not None:
    ahora = datetime.now(ZONA)

    for uid, fecha, asignatura, titulo in leer_tareas():
        dias = (fecha - ahora).days
        nivel = urgencia(dias, titulo)
        emoji = nivel.split()[0]
        titulo_limpio = titulo.removesuffix(" se cierra")

        cuerpo = {
            "summary": f"{emoji} {asignatura}: {titulo_limpio}",
            "description": f"Asignatura: {asignatura}\nUrgencia: {nivel}",
            "start": {"dateTime": (fecha - timedelta(minutes=30)).isoformat(), "timeZone": "Europe/Madrid"},
            "end": {"dateTime": fecha.isoformat(), "timeZone": "Europe/Madrid"},
            "colorId": COLORES[nivel],
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": 1440}],
            },
        }

        resultado = guardar_evento(servicio, id_calendario, crear_id(uid), cuerpo)
        print(f"{resultado}: {cuerpo['summary']}")