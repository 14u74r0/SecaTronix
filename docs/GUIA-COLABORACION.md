# Guía de colaboración (Lautaro + Jules + Claude)

## Qué es cada archivo .md
| Archivo | Para qué sirve |
|---|---|
| `README.md` | Explicación del proyecto, arquitectura y Roadmap. Es la fuente de verdad del "qué". |
| `AGENTS.md` | Reglas y zonas de archivos para agentes. Jules lo lee automáticamente. |
| `CLAUDE.md` | Puntero a `AGENTS.md` y al contrato. Claude lo carga solo. |
| `docs/CONTRATO.md` | Interfaces entre componentes: topics/payload MQTT, tablas y vistas, reglas de alerta. |
| `docs/GUIA-COLABORACION.md` | Este archivo: pasos y prompts. |

## Pasos
1. Mergear el PR #3 (reglas + contrato + guía) a `main`.
2. Crear en GitHub, desde `main`, las ramas `jules/feat/simulador`, `jules/feat/grafana` e `claude/arch/logica-infra`.
3. En jules.google.com, elegir el repo `SecaTronix` y lanzar una tarea por rama con los prompts de abajo (una tarea por rama, no mezclar).
4. Claude trabaja en `claude/arch/logica-infra` y abre su propio PR.
5. Revisar cada PR (el diff debe quedar dentro de la zona del dueño) y mergear. Orden sugerido: infra → simulador → grafana.
6. Probar todo junto: `cp .env.example .env && docker compose up -d`, y mirar Grafana en http://localhost:3000.
7. Tildar en el README los pasos 3 y 4 del Roadmap.

## Prompt para Jules — rama `jules/feat/simulador`
```
Leé README.md, JULES.md, AGENTS.md y docs/CONTRATO.md. Trabajá SOLO en simulador/ y sobre la rama jules/feat/simulador.
Tareas:
1. Agregar la variable de entorno ESPECIE (pino|eucalipto, default pino) con curvas de secado distintas por especie.
2. Corregir SIM_SPEED: hoy acelera dos veces (multiplica el decaimiento y además acorta el sleep). Debe acelerar una sola vez y de forma predecible.
3. sensor_trabado: el nodo n05 debe repetir exactamente el mismo valor en las 3 variables.
4. Mantener el payload y los topics tal cual el contrato. No tocar nada fuera de simulador/.
5. Agregar tests con pytest (decaimiento, escenarios, formato del payload) y documentarlos en un comentario del PR.
6. Que la imagen siga construyendo con docker compose build simulador.
Abrí un PR a main con "qué cambió" y "cómo probarlo".
```

## Prompt para Jules — rama `jules/feat/grafana`
```
Leé README.md, JULES.md, AGENTS.md y docs/CONTRATO.md. Trabajá SOLO en grafana/ y sobre la rama jules/feat/grafana.
Tareas:
1. grafana/provisioning/datasources: datasource PostgreSQL (host postgres, credenciales de .env.example).
2. grafana/provisioning/dashboards + grafana/dashboards/secasmart.json con: semáforo de estado (v_estado_camara), curva de secado real vs objetivo (v_curva_secado), temperatura y humedad del aire por nodo (v_lecturas_nodo), tabla de alertas recientes (tabla alertas) y variable/selector de lote.
3. Usar únicamente las vistas y tablas del contrato. Si faltara algo, dejalo anotado en el PR sin tocar db/.
4. El dashboard debe cargar solo al iniciar, sin configuración manual.
Abrí un PR a main con "qué cambió" y "cómo probarlo".
```

## Mi parte (Claude) — rama `claude/arch/logica-infra`
Esquema y vistas en `db/init.sql`, flujos de Node-RED (ingesta, validación, asignación de lote, reglas y alertas) y ajustes de `docker-compose.yml`. Roadmap Paso 3.
