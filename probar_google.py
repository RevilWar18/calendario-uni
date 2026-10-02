import os.path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ---------- CONFIGURACIÓN ----------
PERMISOS = ["https://www.googleapis.com/auth/calendar"]
NOMBRE_CALENDARIO = "Uni - Tareas"
ZONA = ZoneInfo("Europe/Madrid")


# ---------- FUNCIONES ----------
def conectar():
    """Autoriza el programa y devuelve el 'servicio' para hablar con Google Calendar."""
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


def buscar_calendario(servicio, nombre):
    """Busca un calendario por su nombre y devuelve su identificador."""
    lista = servicio.calendarList().list().execute()
    nombres = []
    for cal in lista["items"]:
        nombres.append(cal["summary"])
        if cal["summary"] == nombre:
            return cal["id"]
    print("No encuentro ese calendario. Los que veo son:", nombres)
    return None


# ---------- PROGRAMA PRINCIPAL ----------
servicio = conectar()
id_calendario = buscar_calendario(servicio, NOMBRE_CALENDARIO)

if id_calendario is not None:
    inicio = datetime.now(ZONA) + timedelta(days=1)
    inicio = inicio.replace(hour=10, minute=0, second=0, microsecond=0)
    fin = inicio + timedelta(minutes=30)

    evento = {
        "summary": "Prueba de calendario-uni",
        "description": "Evento creado por mi programa en Python.",
        "start": {"dateTime": inicio.isoformat(), "timeZone": "Europe/Madrid"},
        "end": {"dateTime": fin.isoformat(), "timeZone": "Europe/Madrid"},
        "colorId": "11",
    }

    creado = servicio.events().insert(calendarId=id_calendario, body=evento).execute()
    print("Evento creado:", creado["htmlLink"])