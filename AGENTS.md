# AGENTS.md — reglas para agentes (Jules, Claude) y personas

Proyecto: **SecaSmart**. La fuente de verdad es `README.md` y `docs/CONTRATO.md`.
Roles y convención de ramas: ver `CLAUDE.md` (Claude: `claude/docs|arch|review/<tema>`) y `JULES.md` (Jules: `jules/feat|fix|test/<desc>`).

## Reglas
1. Nunca pushear a `main`. Una rama por tarea (con los prefijos de CLAUDE.md / JULES.md), un PR por rama. El merge lo hace Lautaro.
2. Tocar **solo** los archivos de tu zona (tabla de abajo). Si necesitás un cambio fuera de tu zona, dejalo escrito en el PR; no lo hagas.
3. No cambiar el stack (Python/paho, Mosquitto, Node-RED, PostgreSQL, Grafana, Docker Compose).
4. Respetar `docs/CONTRATO.md` (topics, payload, tablas, vistas). Si algo del contrato no sirve, proponer el cambio en el PR.
5. Todo debe levantar con `cp .env.example .env && docker compose up -d`.
6. Commits chicos, mensaje en español o inglés, descripción del PR con "qué cambió" y "cómo probarlo".

## Zonas (dueños de archivos)
| Rama (ejemplo) | Dueño | Zona exclusiva |
|---|---|---|
| `claude/arch/<tema>`, `claude/docs/<tema>` | Claude | `db/`, `nodered/`, `docker-compose.yml`, `.env.example`, `mosquitto/`, `docs/`, `contratos/`, `simulador/secasmart/contracts/` |
| `jules/feat|fix|test/<desc>` | Jules | `simulador/` (menos `contracts/`), `grafana/` |
| `main` | Lautaro | `README.md` (checklist del Roadmap) |
