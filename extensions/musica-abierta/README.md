# Música Abierta para Orpheon

Extensión de descarga para [Orpheon](https://github.com/kota-zo/Orpheon) que busca grabaciones con licencia abierta en Internet Archive y las guarda para escuchar sin conexión.

## Importante

- **No descarga audio de Spotify ni evita DRM.** Solo usa el título, artista, álbum y duración de la canción para buscar otra grabación en Internet Archive.
- Solo acepta elementos que declaran una URL de licencia **Creative Commons** o **dominio público**.
- Exige coincidencia de título, artista y duración antes de ofrecer un archivo. Orpheon vuelve a validar la duración y el formato.
- La disponibilidad es limitada. La mayoría de la música comercial no tiene una copia con licencia abierta y aparecerá como no disponible.
- Cada grabación conserva su propia licencia. Consulta la página del elemento en Internet Archive antes de reutilizarla o compartirla.

## Dónde se guarda la música

Orpheon descarga el archivo aceptado, lo valida, lo cifra y lo mantiene dentro de su propia biblioteca offline. No queda como un MP3 o FLAC visible en la carpeta Música del teléfono. Este comportamiento protege la biblioteca y lo controla Orpheon, no la extensión.

## Instalar

1. Descarga el ZIP de **Música Abierta** desde su propia página de GitHub Releases.
2. No lo descomprimas.
3. En Orpheon, abre **Ajustes → Extensiones → Instalar desde un archivo**.
4. Selecciona el ZIP y revisa sus dos acciones:
   - `download.source`: ofrecer archivos para la descarga offline;
   - `network`: consultar únicamente `archive.org`.
5. Confirma la advertencia de extensión de terceros.

Después, usa el botón normal de descarga de una canción, álbum, playlist o Canciones que te gustan. Si existe una coincidencia abierta, Orpheon probará el archivo y lo guardará; si no existe, indicará que la fuente no encontró la grabación.

## Cómo evita coincidencias incorrectas

1. Busca elementos de tipo audio con licencia explícita.
2. Compara el artista del elemento con los artistas de la canción.
3. Compara el título del archivo con el título solicitado, tolerando signos y marcas `feat.`.
4. Rechaza archivos sin duración y los que se aparten del margen que valida Orpheon.
5. Solo devuelve FLAC, MP3 o M4A públicos mediante HTTPS.
6. Prioriza FLAC para calidad CD/alta y archivos pequeños MP3/M4A para el modo compacto.

No se marca `isrcMatched`: Internet Archive no garantiza una búsqueda por ISRC y la extensión no afirma haber identificado el máster exacto mediante huella acústica.

## Privacidad

La extensión envía a Internet Archive el título, artista y, cuando ayuda a encontrar el elemento, el álbum. No usa credenciales, no accede a la cuenta de Spotify y no ejecuta código remoto.

## Desarrollo

Desde la raíz del repositorio:

```bash
python3 scripts/build_extensions.py --extension musica-abierta
node --test tests/musica_abierta.test.js
```

El paquete resultante queda en `packages/io.github.lyanvalentinmail_prog.musicaabierta-<versión>.zip`.

## Licencia

El código y el icono de la extensión se publican bajo [MIT](LICENSE). Los archivos que encuentre pertenecen a sus autores y conservan la licencia indicada por Internet Archive.
