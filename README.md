# Marea Nocturna para Orpheon

Una extensión visual importable para [Orpheon](https://github.com/kota-zo/Orpheon). Aplica un estilo oscuro inspirado en el océano sin acceder a la red, la cuenta de Spotify ni los datos del usuario.

## Qué cambia

- Fondo azul marino (`#06131F`) y superficies azul profundo (`#102A3D`).
- Acento turquesa (`#5EEAD4`) para controles, enlaces y selección.
- Texto un 4 % más grande para mejorar la lectura.
- En el modo **Clásico**, ordena las pestañas como Inicio, Biblioteca y Buscar.
- Oculta la línea secundaria de fuente del reproductor Clásico y la cápsula inferior del reproductor Inmersivo. Sus funciones siguen disponibles desde el menú del reproductor.
- Incluye textos en español e inglés.

La opción **Negro AMOLED** de Orpheon sigue teniendo prioridad sobre el fondo de la extensión.

## Instalar en Orpheon

1. Descarga [`io.github.lyanvalentinmail_prog.mareanocturna-1.0.0.zip`](packages/io.github.lyanvalentinmail_prog.mareanocturna-1.0.0.zip).
2. Abre Orpheon y entra en **Ajustes → Extensiones**.
3. Elige **Instalar desde un archivo** y selecciona el ZIP.
4. Revisa el único permiso mostrado: **Cambiar la apariencia** (`ui.style`).
5. Acepta la advertencia de extensión de terceros y pulsa **Instalar**.

Requiere Orpheon `1.0.0-beta.1` o posterior y la versión 1 de su API de extensiones. Para recuperar la apariencia original, desactiva o desinstala **Marea Nocturna** desde **Ajustes → Extensiones → Instaladas → Páginas y más**.

> Importa el archivo `.zip` directamente. No lo descomprimas y no intentes instalarlo como APK.

## Privacidad y seguridad

El paquete solicita solamente `ui.style`. `main.js` no ejecuta lógica: la apariencia está declarada en `manifest.json` y Orpheon la aplica con sus propios componentes. La extensión:

- no solicita acceso de red;
- no lee ni modifica la biblioteca o la cuenta de Spotify;
- no guarda datos;
- no reproduce ni descarga audio;
- no carga código remoto.

## Verificar y construir

Solo requiere Python 3.9 o posterior:

```bash
make test
```

Ese comando valida el manifiesto y el icono, crea un ZIP determinista, comprueba su contenido y confirma que el paquete versionado coincide byte por byte con una compilación nueva.

Comandos individuales:

```bash
make check   # valida los archivos fuente
make build   # genera packages/<id>-<versión>.zip
sha256sum packages/*.zip
```

Para volver a renderizar `icon.png`, instala ImageMagick y ejecuta:

```bash
make icon
```

`assets/icon.svg` conserva la versión vectorial editable de referencia; el renderizador usa primitivas propias de ImageMagick para no depender de un conversor SVG externo.

## Estructura

```text
manifest.json              metadatos, traducciones y estilo declarado
main.js                    script vacío requerido por el formato
icon.png                   icono incluido en el paquete
assets/icon.svg            fuente editable del icono
scripts/build_extension.py validador y empaquetador determinista
tests/test_extension.py    pruebas del manifiesto y del ZIP
packages/*.zip             paquete listo para importar
```

El ZIP contiene solamente los archivos permitidos por Orpheon en la raíz: `manifest.json`, `main.js`, `icon.png`, `LICENSE` y `README.md`.

## Licencia

Código y recursos de esta extensión bajo la [licencia MIT](LICENSE). Orpheon es un proyecto independiente bajo GPL-3.0; esta extensión no está afiliada ni avalada por Orpheon o Spotify.
