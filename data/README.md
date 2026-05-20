# Datos persistentes TC3D Hub

Esta carpeta NO forma parte de la app en si.

Aqui viven los datos reales para que las actualizaciones de codigo no los borren.

## Estructura

- `db/`: base de datos SQLite principal
- `backups/`: copias automaticas de seguridad
- `exports/projects/`: exportaciones futuras de proyectos
- `exports/clients/`: exportaciones futuras de clientes
- `exports/trello/`: exportaciones futuras del tablero

## Importante

- actualizar la app no debe tocar esta carpeta
- en Docker esta carpeta se monta como volumen persistente
- la base real se guarda en `data/db/tc3d_hub.db`
- al arrancar la app se crea una copia automatica en `data/backups/`

## Recomendacion NAS

Haz backup de toda la carpeta `docker/tc3d/data/`.

