# Memoria del TFG — UnivOrch

Fuentes en LaTeX de la memoria del Trabajo Fin de Grado *Un orquestador
de máquinas virtuales para entornos docentes y de investigación.
Prueba de concepto*.

## Estructura

```
docs/memoria/
├── main.tex                 # documento raíz, hace \input de los demás
├── references.bib           # bibliografía en formato BibTeX
├── frontmatter/             # resumen, abstract, agradecimientos, glosario
├── chapters/                # los 5 capítulos del cuerpo
├── appendices/              # los 4 apéndices
├── figures/                 # imágenes (PNG, PDF de Mermaid)
└── template/                # plantilla oficial UMA (fuentes, logos, .sty)
```

La plantilla `template/` es la versión 2.2 (feb 2026) de
[MarioPasc/UMA-TFG-ETSI-Templates](https://github.com/MarioPasc/UMA-TFG-ETSI-Templates),
sin modificar.

## Flujo de trabajo

La fuente LaTeX vive en este repositorio (`docs/memoria/`). Cada vez
que se actualiza, GitHub Actions compila el PDF automáticamente y lo
deja en dos sitios:

- **Enlace estable que el tutor puede abrir directamente en GitHub**:
  [`github.com/clamaveruma/univorch/blob/pdf-preview/memoria.pdf`](https://github.com/clamaveruma/univorch/blob/pdf-preview/memoria.pdf).
  GitHub renderiza el PDF embebido en el navegador. Apunta siempre a la
  última versión compilada.
- **Artefacto descargable**: en la pestaña
  [Actions](https://github.com/clamaveruma/univorch/actions) del repo,
  cada ejecución del workflow `memoria` deja un ZIP con el PDF.
  Se conserva 30 días.

### Cómo cambia algo

1. Yo (o tú) edito los `.tex` en el repositorio desde el devcontainer.
2. `git push` a `main` con los cambios bajo `docs/memoria/`.
3. El workflow `memoria.yml` arranca solo, compila con XeLaTeX y
   reescribe la rama `pdf-preview` con el PDF nuevo. Tarda 1-2 minutos.
4. El enlace estable de arriba ya muestra la versión actualizada.

### El workflow en detalle

- Definido en [`.github/workflows/memoria.yml`](../../.github/workflows/memoria.yml).
- Imagen: la oficial de `xu-cheng/latex-action@v3` (texlive completo).
- Compilador: XeLaTeX vía `latexmk` (necesario por las fuentes OpenType
  Malacitana de la plantilla UMA).
- Dispara: `push` a `main` que toque `docs/memoria/**` o el propio
  fichero del workflow, además del botón **Run workflow** en la
  pestaña Actions (`workflow_dispatch`).
- Publica a la rama `pdf-preview` con un **único commit** que se
  reescribe en cada compilación; no hay historia que mantener allí.

### Compilación local con Docker (opcional)

Para previsualizar sin esperar al CI, desde el devcontainer (o
cualquier máquina con Docker):

```bash
cd docs/memoria
docker run --rm -v "$PWD:/work" -w /work texlive/texlive:latest \
    latexmk -xelatex -file-line-error -interaction=nonstopmode main.tex
```

### Overleaf (pendiente — requiere acción del tutor)

La integración Git con Overleaf es función Pro/Premium. Los alumnos
de grado de la UMA no la tenemos en el plan institucional (cubre
doctorado y profesorado STEM). Cuando el tutor cree el proyecto desde
su cuenta institucional Pro y te invite como Editor, podrás:

- Ver el PDF compilado al instante mientras tecleas en Overleaf.
- Recibir comentarios del tutor directamente sobre el PDF.

El script [`scripts/sync-overleaf.sh`](../../scripts/sync-overleaf.sh)
está listo para sincronizar `docs/memoria/` con un proyecto Overleaf.
Cuando tengamos el ID del proyecto del tutor, basta con cambiar el
valor de `PROJECT_ID` en el script.

## Datos de portada pendientes de confirmar

Antes de la entrega final, revisar en `main.tex` los placeholders:

- Título exacto en inglés (provisional).
- Mención del grado (si aplica).
- Fecha de defensa (provisional: septiembre de 2026).

## Reglas de coherencia con el resto del repositorio

- **Glosario**: la fuente única es `docs/glossary.md`. El fichero
  `frontmatter/glosario.tex` lo transcribe. Si se modifica un término en
  `glossary.md`, hay que propagarlo aquí.
- **Análisis de requisitos**: el apéndice B transcribe
  `docs/requirements.md`. Misma regla de propagación.
- **Decisiones técnicas**: el apéndice C resume `claude/decisiones.md`.
  Misma regla.
- **Capítulo 4 (Desarrollo)**: cuando se redacte, refrescar antes
  `docs/architecture.md` y `docs/diagrams.md` (les faltan Sprint 2
  Pieza 3 y todo Sprint 3).

## Estilo de redacción

- Castellano académico, impersonal o primera persona del plural (no
  primera persona del singular).
- Términos extranjeros en cursiva la primera vez que aparecen, en
  redonda después.
- Citas con `\cite{key}` en el orden de aparición; estilo IEEE
  (numeric, sorted by name-year-title via biblatex).
- Figuras con `\caption` y `\label` siempre; referenciar con `\cref{}`
  o `\Cref{}` para que el cleveref ponga "figura"/"tabla" según
  corresponda.
