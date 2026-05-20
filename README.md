# TC3D Hub

Dashboard operativo modular para "Tu Casa en 3D".

## Stack elegido

- `FastAPI`: backend simple y rapido
- `SQLite`: base de datos local sin complicaciones
- `Jinja + Tailwind CDN`: frontend limpio para MVP
- `Docker Compose`: despliegue rapido en Windows, NAS o VPS

## Arquitectura recomendada

Empieza con una sola app.

- `app`: interfaz + API + logica simple
- `data`: base SQLite y backups
- `n8n`: despues se conecta por API o webhook
- `Anthropic`: despues se usa desde el modulo IA

Esto evita montar un ERP o microservicios antes de tiempo.

## Estructura

```text
TC3D Hub/
├─ app/
│  ├─ main.py
│  ├─ database.py
│  ├─ requirements.txt
│  ├─ Dockerfile
│  ├─ templates/
│  │  └─ index.html
│  └─ static/
│     └─ app.css
├─ data/
├─ .env.example
├─ docker-compose.yml
└─ README.md
```

## MVP incluido

Pantalla unica con 5 bloques:

1. Resumen empresa
2. Proyectos
3. Produccion
4. Accesos rapidos
5. IA

Incluye datos de ejemplo y ya funciona aunque no pongas Anthropic.

## Arranque local

1. Copia `.env.example` a `.env`
2. Si tienes clave de Anthropic, pegala en `.env`
3. Ejecuta:

```powershell
docker compose up --build
```

4. Abre:

[http://localhost:8090](http://localhost:8090)

## Orden exacto de desarrollo

1. Levantar este MVP local
2. Cambiar datos de ejemplo por datos reales
3. Añadir formulario simple para crear proyectos
4. Conectar accesos reales a carpetas/NAS/Trello/WhatsApp
5. Conectar n8n para automatizaciones
6. Añadir login simple si lo vas a exponer fuera
7. Desplegar en NAS o VPS

## Que instalar primero en el NAS

1. `Container Manager` de Synology
2. Carpeta compartida `tc3d-hub`
3. Docker Compose del proyecto
4. Reverse proxy de Synology si quieres acceso web
5. Luego `n8n` si no lo tienes ahi ya

## Despliegue local y online

### Local

- Windows 11 + Docker Desktop
- Ruta compartida para `data`

### NAS Synology

- Copiar proyecto a una carpeta compartida
- Lanzar `docker compose up -d --build`
- Publicar puerto interno o usar reverse proxy

### Online barato

Opciones simples:

- NAS + dominio propio + reverse proxy
- VPS pequeno con Docker
- Tailscale si quieres acceso privado y barato

Para empezar, lo mas simple suele ser:

- uso diario en local
- acceso remoto privado por Tailscale

## Conectar n8n mas adelante

Tres formas simples:

1. `Webhook`: n8n envia datos al dashboard
2. `Polling`: dashboard consulta una tabla o endpoint
3. `SQLite/API`: n8n escribe proyectos, tareas o entregables

Recomendacion MVP:

- que n8n escriba en SQLite via API HTTP del dashboard

## Conectar Anthropic API

1. Pon la clave en `.env`
2. Usa el bloque IA del dashboard
3. El backend llama a Anthropic y devuelve texto

Usos iniciales recomendados:

- resumir reuniones
- redactar emails
- sacar tareas
- generar ideas rapidas

## Backups simples

Empieza con esto:

1. Backup diario de la carpeta `data/`
2. Copia al NAS
3. Opcional: Synology Hyper Backup a otra ubicacion

Como `SQLite` es un solo archivo, el backup es muy facil.

## Siguiente paso recomendado

Levanta el MVP, prueba la interfaz y luego cambiamos juntos:

- campos reales
- estados reales
- accesos rapidos reales
- automatizaciones con n8n

