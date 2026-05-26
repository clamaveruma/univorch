# Proyecto: Orquestador Universal de Máquinas Virtuales

## Descripción

Prueba de concepto de un orquestador universal de máquinas virtuales orientado a entornos docentes y de investigación.

El objetivo es proporcionar una capa de abstracción que permita gestionar VMs de forma unificada, independientemente del hipervisor o plataforma subyacente, adaptada a las necesidades específicas de aulas y laboratorios de investigación.

## Estado actual

- Fase: 6 — Desarrollo iterativo. Sprint 1 (núcleo mínimo + CLI) **completado**;
  Sprint 2 (herencia en cascada / Resolver + web GUI) pendiente. Detalle en `claude/diario.md`.
- Stack tecnológico (Fase 4): Python 3.12 · uv · pytest + Hypothesis · Ruff + mypy ·
  TinyDB (futuro MongoDB) · cmd2 (CLI) · NiceGUI (web, Sprint 2) · FastAPI + uvicorn + httpx
  (REST, Sprint 2) · pyvmomi / proxmoxer (conectores reales, Sprint 3+). Ver `docs/technologies.md`.
- Repositorio: clamaveruma/univorch

## Objetivos principales

- Orquestar VMs de forma agnóstica al hipervisor
- Adaptado a entornos docentes (aulas, laboratorios)
- Adaptado a entornos de investigación
- Prueba de concepto funcional

## Contexto y restricciones

- Las decisiones de diseño se trazan en `claude/decisiones.md` (DEC-001 a DEC-035).
- Marco de proceso en 7 fases: ver `docs/plan.md`.
