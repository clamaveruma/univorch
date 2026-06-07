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

## Flujo de trabajo: edición en el repositorio, compilación en Overleaf

La fuente vive aquí, en el repositorio. Para visualizar el PDF y
compartir con el tutor se usa Overleaf, sincronizado con el repositorio
de GitHub.

### Una sola vez: configurar el proyecto en Overleaf

1. Crear cuenta en [overleaf.com](https://www.overleaf.com) con correo
   institucional UMA (terminado en `@uma.es` o `@alumno.uma.es`). Esto
   activa la cuenta Pro gratis, necesaria para sincronizar con GitHub.
2. Crear un proyecto nuevo en Overleaf: menú **New Project > Import from
   GitHub**. Autorizar Overleaf en GitHub si lo pide.
3. Seleccionar el repositorio `clamaveruma/univorch`.
4. Cuando Overleaf abra el proyecto, en la barra lateral izquierda
   pulsar el icono de carpeta y navegar a `docs/memoria/`.
5. Marcar `docs/memoria/main.tex` como **Main document** (botón
   derecho > Set as main document).
6. En **Menu > Compiler**, seleccionar `XeLaTeX` o `LuaLaTeX` (la
   plantilla usa fuentes OpenType Malacitana).

### Día a día

- **Yo edito** los `.tex` en el repositorio desde el devcontainer y
  hago `git push`.
- **Tú abres Overleaf**, pulsas **Menu > Sync > GitHub > Pull from
  GitHub**. Overleaf descarga los cambios y recompila.
- Si **el tutor** quiere comentar: en Overleaf, **Share > Add People**,
  poner su correo, rol **Review** (puede comentar sin tocar el texto).
- Si **tú** modificas algo en Overleaf, **Push to GitHub** sube los
  cambios al repositorio. Yo los recojo con `git pull`.

### Compilación local con Docker (opcional)

Cuando llegue el momento, se añadirá un workflow de GitHub Actions que
compile el PDF con la imagen oficial `texlive/texlive` y lo deje como
artefacto del release. Mientras tanto, para compilar localmente sin
Overleaf:

```bash
cd docs/memoria
docker run --rm -v "$PWD:/work" -w /work texlive/texlive:latest \
    latexmk -xelatex -file-line-error -interaction=nonstopmode main.tex
```

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
