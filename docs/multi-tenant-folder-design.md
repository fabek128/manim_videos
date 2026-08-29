# Diseño multi-tenant por carpetas

## Objetivo

Convertir `redes2` en una aplicación multi-tenant sin base de datos, servicios nuevos, contenedores ni symlinks. Cada tenant tendrá marca, assets, configuraciones, escenas, contenido y resultados aislados. El código, los scripts, los themes y la documentación técnica permanecerán compartidos.

El primer tenant será `agente32`:

- Marca: **Agente E32**.
- Cuenta principal: **@fabian128k**.
- Tenant por defecto: `agente32`.

## Decisión

Usar una carpeta fija por tenant:

```text
tenants/<tenant_id>/
```

No introducir una base de datos. El filesystem será la fuente de verdad para identidad, configuraciones, contenido y outputs. El tenant activo se resolverá con esta precedencia:

1. Argumento CLI `--tenant`.
2. Variable de entorno `TENANT`.
3. Variable `DEFAULT_TENANT` del `.env` raíz.

Para conservar el uso actual, `.env` configurará:

```env
DEFAULT_TENANT=agente32
```

## Estructura propuesta

```text
redes2/
├── AGENTS.md
├── README.md
├── .env                         # configuración/proveedores compartidos
├── .env.example
├── build.py                     # compartido
├── scripts/                     # compartido
│   ├── generate_images.py
│   ├── generate_videos.py
│   ├── promptgate_client.py
│   └── publish_final.py
├── src/                         # compartido
│   └── noticia_carrusel/
├── templates/                   # compartido
│   └── prompts/
├── skills/                      # compartido
├── utils/                       # compartido
├── docs/                        # compartido
├── assets/                      # assets compartidos
│   ├── fonts/
│   └── logos/                   # logos genéricos/proveedores
└── tenants/
    └── agente32/
        ├── tenant.yaml
        ├── .env                 # secretos/configuración exclusiva, gitignored
        ├── .env.example
        ├── assets/
        │   ├── logos/
        │   ├── images/
        │   └── sounds/
        ├── configs/
        │   ├── images/
        │   └── videos/
        ├── videos/
        │   ├── lostops/
        │   └── ...
        ├── media/               # trabajo generado por Manim/scripts
        │   ├── videos/
        │   ├── images/
        │   └── posts/
        └── output/              # imágenes finales aún no publicadas
```

### Carpetas compartidas

Permanecen en raíz:

- `scripts/`.
- `src/`.
- `templates/prompts/`.
- `skills/`.
- `utils/`.
- `docs/`.
- `assets/fonts/`.
- Logos genéricos de proveedores, si pueden reutilizarse entre tenants.

### Carpetas del tenant

Viven dentro de `tenants/agente32/`:

- Logo y recursos propios de Agente E32.
- Recursos de `@fabian128k`.
- Configuraciones YAML/JSON de imágenes y carruseles.
- Escenas y JSON de videos.
- Música o sonidos propios.
- Outputs de trabajo.
- Textos de posts generados.
- Credenciales de redes sociales exclusivas del tenant.

## Manifest mínimo

Archivo `tenants/agente32/tenant.yaml`:

```yaml
id: agente32
name: "Agente E32"

brand:
  logo: "logos/agente32.svg"
  default_theme: "theme_default"

social:
  instagram:
    handle: "@fabian128k"

publish:
  namespace: "agente32"
```

Las rutas de carpetas no se declaran en el YAML: siguen una convención fija. Esto evita configuración repetida y reduce errores.

No guardar secretos en `tenant.yaml`.

## Resolución de tenant

Crear un único módulo compartido:

```text
src/noticia_carrusel/tenant.py
```

Responsabilidad:

```python
@dataclass(frozen=True)
class TenantContext:
    id: str
    root: Path
    manifest: TenantManifest

    @property
    def assets_dir(self) -> Path: ...

    @property
    def configs_dir(self) -> Path: ...

    @property
    def videos_dir(self) -> Path: ...

    @property
    def media_dir(self) -> Path: ...

    @property
    def output_dir(self) -> Path: ...

    def resolve_asset(self, relative: str) -> Path: ...
    def resolve_inside(self, base: Path, relative: str) -> Path: ...
```

Función pública:

```python
def load_tenant(tenant_id: str | None = None) -> TenantContext:
    """CLI > TENANT > DEFAULT_TENANT."""
```

### Reglas de seguridad

- `tenant_id` debe cumplir `^[a-z0-9][a-z0-9_-]*$`.
- `tenants/<tenant_id>` debe existir.
- Toda ruta de escritura debe permanecer dentro de la carpeta del tenant.
- Rechazar `..`, paths absolutos no autorizados y escapes mediante `resolve()`.
- La única escritura externa permitida es la publicación explícita en `FINAL_OUTPUT_DIR` después de aprobación.
- Los assets compartidos son solo lectura.

## Resolución de assets

Aplicar una única regla:

1. Buscar en `tenants/<tenant>/assets/<ruta>`.
2. Si no existe, buscar en `assets/<ruta>` compartido.
3. Si no existe, fallar con un mensaje que muestre ambos paths intentados.

Ejemplo de configuración:

```yaml
brand:
  logo_path: "logos/agente32.svg"

fonts:
  title: "fonts/Montserrat-ExtraBold.ttf"
  body: "fonts/Inter-SemiBold.ttf"
  code: "fonts/FiraCode-Regular.ttf"
```

No usar `../assets/...` dentro de configuraciones tenant. El resolver decide si el asset es propio o compartido.

## Configuración y secretos

### `.env` raíz

Solo configuración compartida o de infraestructura:

- `DEFAULT_TENANT`.
- PromptGate.
- Modelos por defecto.
- OpenRouter si la misma cuenta y facturación se comparte entre tenants.

### `tenants/agente32/.env`

Solo configuración exclusiva del tenant:

- Credenciales Meta/Instagram.
- Destino de publicación propio.
- Overrides de modelos, si fueran necesarios.

Carga recomendada:

1. Variables ya exportadas por el proceso.
2. `.env` raíz para defaults compartidos.
3. `.env` del tenant para configuración específica.

El loader debe definir con claridad si el tenant puede sobrescribir defaults compartidos. Recomendación: permitir override únicamente para una lista explícita de variables configurables; las variables exportadas por el proceso conservan prioridad.

Agregar a `.gitignore`:

```gitignore
tenants/*/.env
```

Agregar un `.env.example` sin valores sensibles por tenant. Los `.env` reales deben conservar permisos `600`.

## Cambios por componente

### `scripts/generate_images.py`

Agregar argumento global:

```bash
python scripts/generate_images.py --tenant agente32 post \
  --config noticia_malaponte/post_vertical.yaml
```

Comportamiento:

- Cargar `TenantContext`.
- Resolver el config relativo a `tenant.configs_dir / "images"`.
- Resolver assets mediante `TenantContext.resolve_asset()`.
- Ignorar cualquier `output_dir` que escape del tenant.
- Guardar en `tenant.output_dir/<project_name>/`.

Sin `--tenant`, debe usar `DEFAULT_TENANT=agente32`.

### `scripts/generate_videos.py` y `build.py`

Agregar `--tenant` y resolver:

```python
VIDEOS_DIR = tenant.videos_dir
MEDIA_DIR = tenant.media_dir
POSTS_DIR = tenant.media_dir / "posts"
```

Comando:

```bash
python scripts/generate_videos.py --tenant agente32 \
  --video lostops --no-preview
```

Las escenas que hoy calculan assets mediante `Path(__file__).parents[...]` deben usar el resolver de tenant. Ninguna escena debe asumir que `assets/` está a una cantidad fija de niveles.

### `src/noticia_carrusel/models.py`

Cambiar el significado de `output_dir`:

- Debe ser un path relativo al `output/` del tenant.
- Rechazar paths absolutos y `..`.
- Alternativa más simple: hacerlo opcional y usar `project_name` como nombre de carpeta.

Recomendación:

```yaml
project_name: "noticia_malaponte_vertical"
output_dir: "noticia_malaponte_vertical"
```

### `src/noticia_carrusel/config.py`

Recibir `TenantContext` para resolver:

- config;
- logo;
- fuentes;
- imagen de fondo;
- output.

No resolver contra la ubicación física del YAML mediante `../`.

### `src/noticia_carrusel/render/templates.py`

Reemplazar paths derivados de `config_path.parent` por paths ya resueltos desde `TenantContext`.

La composición, los presets y los themes siguen siendo compartidos.

### `scripts/publish_final.py`

Agregar `--tenant` y leer únicamente:

```text
tenants/<tenant>/media/
tenants/<tenant>/output/
```

Publicar en un namespace aislado:

```text
/Users/fabian/Documents/shared/
└── agente32/
    ├── videos/<YYYY-MM-DD>_<slug>/
    └── images/<YYYY-MM-DD>_<slug>/
```

La publicación sigue requiriendo aprobación explícita del usuario. No se activa desde los generadores.

## Themes compartidos

Los themes permanecen en:

```text
templates/prompts/
```

El manifest del tenant selecciona el theme por nombre:

```yaml
brand:
  default_theme: "theme_default"
```

No crear copias por tenant. Si más adelante un tenant necesita un override, agregarlo como una necesidad real; no anticiparlo en la primera migración.

## Migración de Agente E32

### 1. Crear estructura

```text
tenants/agente32/
├── tenant.yaml
├── .env.example
├── assets/
├── configs/images/
├── configs/videos/
├── videos/
├── media/
└── output/
```

### 2. Mover configuraciones de imágenes

```text
examples/*.yaml
→ tenants/agente32/configs/images/*.yaml
```

Actualizar configuraciones:

- Eliminar `../assets/`.
- Usar paths lógicos como `fonts/...` y `logos/...`.
- Convertir `output_dir` a path relativo del tenant.

### 3. Mover recursos propios

```text
assets/logos/agente32/
→ tenants/agente32/assets/logos/agente32/
```

Mover también recursos exclusivos de `fabian128k` y sonidos de marca. Mantener fuentes y logos genéricos en `assets/` compartido.

### 4. Mover videos

```text
videos/
→ tenants/agente32/videos/
```

Actualizar escenas para usar `TenantContext`.

### 5. Mover outputs de trabajo

```text
media/
→ tenants/agente32/media/

output/
→ tenants/agente32/output/
```

No migrar archivos temporales obsoletos; conservar únicamente outputs útiles.

### 6. Dividir `.env`

- Mantener configuración compartida en raíz.
- Mover variables exclusivas de Agente E32 al `.env` del tenant.
- No documentar valores.
- Verificar permisos y `.gitignore`.

### 7. Actualizar scripts

Orden:

1. Implementar `TenantContext` y sus tests.
2. Actualizar generador de imágenes.
3. Actualizar publicador.
4. Actualizar builder de videos.
5. Actualizar escenas.

### 8. Corte limpio

Después de verificar todos los comandos, eliminar las rutas tenant-specific de raíz. No mantener fallback permanente a `examples/`, `videos/`, `media/` u `output/`.

El único mecanismo de compatibilidad será `DEFAULT_TENANT=agente32`, que permite seguir ejecutando comandos sin escribir `--tenant`.

## Comandos finales

```bash
# Tenant por defecto
python scripts/generate_images.py post \
  --config noticia_malaponte/post_vertical.yaml

# Tenant explícito
python scripts/generate_images.py --tenant agente32 carousel \
  --config noticia_malaponte/carousel_vertical.yaml

python scripts/generate_videos.py --tenant agente32 \
  --video lostops --no-preview

# Publicación posterior a aprobación
python scripts/publish_final.py --tenant agente32 \
  --type images \
  --source tenants/agente32/output/noticia/slide_01.png \
  --date 2026-08-28 \
  --slug noticia
```

## Validaciones de aislamiento

Agregar smoke tests que prueben:

1. `agente32` carga correctamente.
2. Tenant inexistente falla antes de leer o escribir.
3. `--tenant ../otro` se rechaza.
4. Un `output_dir: ../../fuera` se rechaza.
5. Un asset propio tiene prioridad sobre el compartido.
6. Un asset compartido se usa como fallback de lectura.
7. Un config de Agente E32 no puede escribir dentro de otro tenant.
8. `build.py` descubre solo las escenas del tenant activo.
9. `publish_final.py` publica dentro del namespace del tenant.
10. La ejecución sin `--tenant` usa `DEFAULT_TENANT=agente32`.

## Riesgos

### Rutas relativas existentes

Las configuraciones actuales usan `../assets/...`. Deben migrarse a rutas lógicas antes del corte.

### Escenas Manim acopladas al árbol

Varias escenas calculan assets con `Path(__file__).parents[...]`. Deben usar el resolver común.

### Secretos mezclados

El `.env` actual contiene variables compartidas y de marca. La migración debe separar nombres y scopes sin imprimir valores.

### Colisiones de publicación

Dos tenants podrían usar el mismo slug y fecha. El namespace del tenant en `FINAL_OUTPUT_DIR` evita la colisión.

### Duplicación de assets

Mover únicamente assets propios. Las fuentes y logos de proveedores permanecen compartidos para evitar copias innecesarias.

## Qué no implementar

- Base de datos de tenants.
- Panel de administración.
- API web.
- Contenedores por tenant.
- Symlinks.
- Plugins dinámicos.
- Herencia de themes por tenant.
- Permisos complejos dentro de la aplicación.

Estas capacidades no son necesarias para el primer tenant y aumentarían el costo de mantenimiento.

## Criterios de aceptación

1. Existe `tenants/agente32/tenant.yaml` y valida.
2. Los scripts aceptan `--tenant agente32`.
3. Sin `--tenant`, se usa `DEFAULT_TENANT=agente32`.
4. Imágenes, videos, posts y outputs se escriben solo en carpetas de Agente E32.
5. Scripts, código, themes y fuentes compartidas permanecen en raíz.
6. El logo y recursos propios se resuelven desde el tenant.
7. Las rutas con traversal o escapes se rechazan.
8. Los secretos específicos viven en `tenants/agente32/.env`, están gitignored y tienen permisos `600`.
9. La publicación final queda en `/Users/fabian/Documents/shared/agente32/...` y solo se ejecuta después de aprobación.
10. No quedan directorios tenant-specific duplicados en raíz después del corte.
11. Los comandos actuales siguen funcionando mediante el tenant por defecto.
12. No se introducen servicios, base de datos, contenedores ni symlinks.

## Conclusión

La migración más simple es un corte limpio hacia `tenants/<id>/`, con una única clase `TenantContext`, carpetas de convención fija y `agente32` como tenant por defecto. Esto aísla configuración, marca, contenido y outputs sin cambiar la arquitectura técnica del proyecto ni añadir infraestructura.
