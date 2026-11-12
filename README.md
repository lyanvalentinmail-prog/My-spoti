# Extensiones de Orpheon

Este repositorio contiene **dos extensiones independientes** para [Orpheon](https://github.com/kota-zo/Orpheon). Cada una tiene su propio manifiesto, código, icono, paquete ZIP, workflow y página de GitHub Release. Puedes instalar una sin instalar la otra.

## Extensiones

### 🌊 Marea Nocturna

Tema oscuro oceánico con acentos turquesa, reproductores más limpios y texto ligeramente mayor. No usa red ni accede a datos.

- Fuente: [`extensions/marea-nocturna`](extensions/marea-nocturna)
- Release: [Marea Nocturna 1.0.0](https://github.com/lyanvalentinmail-prog/My-spoti/releases/tag/marea-nocturna-v1.0.0)
- ZIP: [`io.github.lyanvalentinmail_prog.mareanocturna-1.0.0.zip`](https://github.com/lyanvalentinmail-prog/My-spoti/releases/download/marea-nocturna-v1.0.0/io.github.lyanvalentinmail_prog.mareanocturna-1.0.0.zip)

### 📥 Música Abierta

Fuente de descarga que busca grabaciones coincidentes con licencia Creative Commons o de dominio público en Internet Archive. Orpheon valida, cifra y guarda el archivo dentro de su biblioteca offline.

- **No descarga audio de Spotify ni evita DRM.**
- La mayoría de las canciones comerciales no están disponibles con licencia abierta.
- Fuente: [`extensions/musica-abierta`](extensions/musica-abierta)
- Release: [Música Abierta 1.0.0](https://github.com/lyanvalentinmail-prog/My-spoti/releases/tag/musica-abierta-v1.0.0)
- ZIP: [`io.github.lyanvalentinmail_prog.musicaabierta-1.0.0.zip`](https://github.com/lyanvalentinmail-prog/My-spoti/releases/download/musica-abierta-v1.0.0/io.github.lyanvalentinmail_prog.musicaabierta-1.0.0.zip)

## Instalarlas por separado

Para cada extensión que quieras usar:

1. Descarga **solo su ZIP** desde la release correspondiente. No necesitas descargar el repositorio.
2. No descomprimas el archivo.
3. Abre **Orpheon → Ajustes → Extensiones → Instalar desde un archivo**.
4. Selecciona el ZIP y revisa las acciones solicitadas.
5. Confirma la instalación de terceros.

Los dos ZIP tienen identificadores distintos, por lo que pueden estar instalados a la vez y se activan, desactivan o desinstalan por separado.

## Construcción y pruebas

Requisitos locales: Python 3.9+ y Node.js 20+; no hay dependencias que instalar.

```bash
make test
```

Comandos por extensión:

```bash
python3 scripts/build_extensions.py --extension marea-nocturna
python3 scripts/build_extensions.py --extension musica-abierta
```

Los paquetes reproducibles se escriben en `packages/`. Cada ZIP contiene únicamente los archivos que permite Orpheon en su raíz: `manifest.json`, `main.js`, `icon.png`, `LICENSE` y `README.md`.

## Workflows y Releases

Los workflows son independientes:

- **Marea Nocturna** construye y publica etiquetas `marea-nocturna-v*`.
- **Música Abierta** construye y publica etiquetas `musica-abierta-v*`.

En cada ejecución se puede descargar únicamente el artefacto ZIP de esa extensión. Al crear su etiqueta, el workflow valida que la versión de la etiqueta coincida con `manifest.json` y adjunta el ZIP a una release separada.

## Licencia

Las extensiones y herramientas de este repositorio se publican bajo [MIT](LICENSE). Los audios encontrados por Música Abierta pertenecen a sus autores y mantienen la licencia indicada en Internet Archive. Orpheon y Spotify son proyectos y marcas independientes; este repositorio no está afiliado ni avalado por ellos.
