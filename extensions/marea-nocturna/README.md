# Marea Nocturna para Orpheon

Una extensión visual instalable para [Orpheon](https://github.com/kota-zo/Orpheon). Aplica un estilo oscuro inspirado en el océano sin acceder a la red, la cuenta de Spotify ni los datos del usuario.

## Qué cambia

- Fondo azul marino (`#06131F`) y superficies azul profundo (`#102A3D`).
- Acento turquesa (`#5EEAD4`) para controles, enlaces y selección.
- Texto un 4 % más grande para mejorar la lectura.
- En el modo **Clásico**, ordena las pestañas como Inicio, Biblioteca y Buscar.
- Oculta la línea secundaria de fuente del reproductor Clásico y la cápsula inferior del reproductor Inmersivo. Sus funciones siguen disponibles desde el menú del reproductor.
- Incluye textos en español e inglés.

La opción **Negro AMOLED** de Orpheon sigue teniendo prioridad sobre el fondo de la extensión.

## Instalar

1. Descarga el ZIP de **Marea Nocturna** desde su propia página de GitHub Releases.
2. No lo descomprimas.
3. Abre Orpheon y entra en **Ajustes → Extensiones**.
4. Elige **Instalar desde un archivo** y selecciona el ZIP.
5. Revisa su única acción: **Cambiar la apariencia** (`ui.style`).
6. Acepta la advertencia de extensión de terceros y pulsa **Instalar**.

Requiere Orpheon `1.0.0-beta.1` o posterior y la versión 1 de su API de extensiones. Para recuperar la apariencia original, desactiva o desinstala **Marea Nocturna** desde **Ajustes → Extensiones → Instaladas → Páginas y más**.

## Privacidad y seguridad

El paquete solicita solamente `ui.style`. `main.js` no ejecuta lógica: la apariencia está declarada en `manifest.json` y Orpheon la aplica con sus propios componentes. La extensión:

- no solicita acceso de red;
- no lee ni modifica la biblioteca o la cuenta de Spotify;
- no guarda datos;
- no reproduce ni descarga audio;
- no carga código remoto.

## Desarrollo

Desde la raíz del repositorio:

```bash
python3 scripts/build_extensions.py --extension marea-nocturna
```

El paquete resultante queda en `packages/io.github.lyanvalentinmail_prog.mareanocturna-<versión>.zip`.

Para regenerar el icono con ImageMagick:

```bash
bash scripts/render_icons.sh marea-nocturna
```

## Licencia

Código y recursos de esta extensión bajo la [licencia MIT](LICENSE). Orpheon es un proyecto independiente bajo GPL-3.0; esta extensión no está afiliada ni avalada por Orpheon o Spotify.
