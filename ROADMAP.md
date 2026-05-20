# ROADMAP - TC3D Hub

## Vision

Crear un dashboard operativo modular, rapido y muy simple para "Tu Casa en 3D".

Objetivo real:

- centralizar trabajo diario
- reducir clics
- ver estado del estudio en 1 pantalla
- automatizar tareas pequeñas
- crecer por modulos, sin montar un ERP

## Principios del proyecto

- primero utilidad, luego complejidad
- una sola app mientras sea posible
- modulos independientes
- datos simples
- Docker desde el inicio
- compatible con Windows, NAS Synology y acceso web
- bajo coste y mantenimiento facil

## Stack elegido

- `FastAPI`
- `SQLite`
- `Jinja`
- `TailwindCSS`
- `Docker Compose`
- `Anthropic API`
- `n8n` mas adelante

## Estado actual

Ya existe un MVP funcional con:

- resumen empresa
- proyectos en tabla
- panel de produccion
- accesos rapidos
- bloque IA
- modulo de trabajo tipo mini-Trello
- reuniones con checklist

## Arquitectura recomendada

### Fase inicial

Una sola app:

- `frontend`: dashboard y formularios
- `backend`: API y logica simple
- `sqlite`: base local en archivo

### Fase de crecimiento

Seguir con esta estructura:

- `dashboard`: interfaz principal
- `trabajo`: proyectos, reuniones, tareas
- `produccion`: renders, cola, equipos
- `finanzas`: facturacion, cobros, presupuestos
- `ia`: ayudas operativas
- `integraciones`: n8n, Trello, WhatsApp, NAS

No separar en microservicios de momento.

## Estructura deseada

```text
TC3D Hub/
├─ app/
│  ├─ main.py
│  ├─ database.py
│  ├─ templates/
│  ├─ static/
│  └─ requirements.txt
├─ data/
├─ docker-compose.yml
├─ README.md
├─ ROADMAP.md
└─ .env
```

## Modulos del sistema

### 1. Resumen empresa

Objetivo:

- ver negocio en 20 segundos

Campos:

- facturacion del mes
- proyectos activos
- presupuestos pendientes
- cobros pendientes
- proximos entregables

### 2. Trabajo

Objetivo:

- controlar el trabajo diario sin depender siempre de Trello

Submodulos:

- tablero por estados
- lista de proyectos
- reuniones
- checklist de tareas

Estados iniciales recomendados:

- pendiente inicio
- en produccion
- revision cliente
- completado

Evolucion recomendada:

- responsable
- prioridad
- fecha interna
- fecha entrega cliente
- etiquetas
- arrastrar entre columnas

### 3. Produccion

Objetivo:

- ver carga real del estudio

Campos:

- renders pendientes
- horas estimadas
- PCs disponibles
- cola render

Evolucion recomendada:

- equipo por PC
- estado de render por maquina
- tiempo estimado vs real

### 4. Accesos rapidos

Objetivo:

- abrir recursos clave sin navegar

Ejemplos:

- carpetas locales
- carpetas NAS
- Trello
- WhatsApp
- presupuestos
- fichas cliente

### 5. IA

Objetivo:

- usar IA solo para tareas que ahorran tiempo

Usos iniciales:

- resumir reuniones
- redactar emails
- convertir notas en tareas
- ideas rapidas

Usos siguientes:

- preparar brief de proyecto
- responder feedback cliente
- crear checklist desde reunion

## Hoja de ruta por fases

### Fase 1 - Base operativa

Estado: en marcha

Objetivo:

- tener algo funcional en 1-2 dias

Entregables:

- dashboard visible
- SQLite funcionando
- Docker funcionando
- tablero de proyectos
- reuniones con checklist

### Fase 2 - Trabajo real diario

Prioridad: muy alta

Objetivo:

- convertir el MVP en herramienta usable cada dia

Tareas:

- adaptar estados a vuestro flujo real
- añadir responsables
- añadir prioridad
- diferenciar fecha interna y entrega final
- mejorar tarjeta de proyecto
- permitir editar proyectos
- permitir editar reuniones y tareas

### Fase 3 - Integraciones utiles

Prioridad: alta

Objetivo:

- ahorrar pasos manuales

Tareas:

- conectar `n8n`
- crear webhooks simples
- importar tareas desde emails o formularios
- generar resumen de reunion con IA
- guardar salida de IA en proyecto o reunion

### Fase 4 - Operacion NAS

Prioridad: alta

Objetivo:

- dejarlo estable en Synology

Tareas:

- desplegar en `docker/tc3d`
- persistir `data/`
- reverse proxy si hace falta
- acceso por dominio o subdominio interno
- backup diario de datos

### Fase 5 - Apertura web controlada

Prioridad: media

Objetivo:

- acceso remoto seguro

Tareas:

- login simple
- usuario y contraseña
- HTTPS
- acceso por VPN o Tailscale si prefieres menos exposicion

## Orden exacto de desarrollo recomendado

1. fijar flujo real de trabajo
2. cerrar modulo trabajo
3. desplegar en NAS
4. versionar en GitHub
5. conectar IA a trabajo
6. conectar `n8n`
7. mejorar produccion
8. mejorar finanzas

## Lo que haria justo ahora

### Sprint 1

- revisar estados reales contigo
- añadir responsable y prioridad
- desplegar en NAS
- subir a GitHub

### Sprint 2

- editar y borrar tareas
- editar reuniones
- filtros por estado
- generacion de tareas desde IA

### Sprint 3

- webhook de `n8n`
- entrada automatica de leads, reuniones o tareas
- backup automatizado en NAS

## Modelo de datos recomendado a corto plazo

### Tabla `projects`

- cliente
- proyecto
- estado
- entrega
- importe
- notas

### Tabla futura `project_tasks`

- proyecto_id
- titulo
- estado
- prioridad
- responsable
- fecha_limite

### Tabla `meetings`

- titulo
- cliente
- fecha
- notas

### Tabla `meeting_tasks`

- meeting_id
- texto
- hecho

## Despliegue NAS recomendado

Ruta objetivo:

- `docker/tc3d`

Contenido esperado:

- `docker-compose.yml`
- carpeta `app`
- carpeta `data`
- `.env`

Proceso:

1. copiar proyecto al NAS
2. entrar por `SSH`
3. ir a `docker/tc3d`
4. lanzar `docker compose up -d --build`
5. validar puerto y acceso web

## GitHub recomendado

Objetivo:

- tener historial
- permitir continuidad con Claude o cualquier otra IA
- poder volver atras

Estructura recomendada:

- repo: `tc3d-hub`
- branch principal: `main`
- commits cortos y claros

Commits tipo:

- `base mvp dashboard`
- `add work board and meeting checklist`
- `prepare synology deployment`

## Backups simples

### Minimo recomendable

- backup diario de `data/`
- copia en NAS

### Mejor opcion

- Hyper Backup del NAS sobre carpeta `docker/tc3d/data`

## Bloqueos actuales

### NAS

- el acceso `SSH` con `deploy-tmp` ha rechazado la contraseña actual

### GitHub

- esta carpeta aun no es repo Git
- no hay remoto configurado
- no está instalado `gh` en esta máquina

## Siguiente objetivo practico

Dejar el sistema en este orden:

1. repo Git creado
2. repo GitHub enlazado
3. acceso NAS confirmado
4. despliegue en NAS
5. estados reales de trabajo adaptados

