# editor-video-ia

Skill para editar videos grabados a cámara y sacar reels verticales con Remotion: cortes, subtítulos,
tarjetas animadas, zooms, música con ducking y render a MP4.

## Instalación

1. Copia `config.example.json` a `config.json` y pon tu proveedor y tu clave. Este archivo no se sube.
2. Motor (Remotion): `cd engine && npm install`
3. Python: crea un entorno virtual en `.venv/` e instala lo que pidan los scripts de `scripts/`.

`SKILL.md` describe el flujo completo y `references/` tiene la documentación de cada efecto y preset.

## Novedades

- `prep.py` guarda una huella (video + modelo + idioma) y no vuelve a transcribir si no cambió nada. `--recalcular` fuerza la transcripción.
- `render.sh --dry-run` imprime los pasos sin renderizar. `render.sh --preview` renderiza un borrador a 480p y 15 fps para validar el plan.
