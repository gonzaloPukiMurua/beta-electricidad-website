# Electricidad App — Technical Summary
> Documento de referencia para continuar el proyecto en un nuevo chat.
> Estado al: junio 2026

---

## 1. Contexto del negocio

Negocio de electricidad retail/mayorista en La Falda, Córdoba, Argentina.
Sistema ERP local Visual FoxPro (sin conexión a internet).
Objetivo: e-commerce + portal de presupuestos self-service para clientes.

---

## 2. Stack definido

| Capa | Tecnología | Estado |
|---|---|---|
| ERP origen | Visual FoxPro / DBF | Existente, solo lectura |
| Base de datos web | Supabase (Postgres) | ✅ Activo, tabla cargada |
| Autenticación | Supabase Auth | ✅ Configurado |
| Frontend / Admin | Next.js (App Router) + TypeScript + Tailwind | 🔜 Próximo sprint |
| Backend API | A definir — Supabase directo o NestJS | Decisión pendiente |
| Scripts sync | Python 3.14 local | ✅ En producción |

---

## 3. Base de datos Supabase

### Tabla: `productos`

```sql
CREATE TABLE productos (
    id              BIGSERIAL PRIMARY KEY,
    codigo          INTEGER UNIQUE NOT NULL,
    codigo_alt      TEXT,
    nombre          TEXT NOT NULL,
    rubro           TEXT,
    marca           TEXT,
    precio_venta    NUMERIC(12, 2),
    costo           NUMERIC(12, 2),
    stock           NUMERIC(10, 2),
    publicado_web   BOOLEAN DEFAULT FALSE,
    en_oferta       BOOLEAN DEFAULT FALSE,
    activo          BOOLEAN DEFAULT TRUE,
    -- 17 columnas de listas de precio:
    lista_normal              NUMERIC(12, 2),
    lista_dto_especial        NUMERIC(12, 2),
    lista_tarjeta_6_cuotas    NUMERIC(12, 2),
    lista_debito              NUMERIC(12, 2),
    lista_gremio_instalador   NUMERIC(12, 2),
    lista_dto_gremio_espec    NUMERIC(12, 2),
    lista_tarjeta_3_cuotas    NUMERIC(12, 2),
    lista_tarjeta_2_cuotas    NUMERIC(12, 2),
    lista_getnet_1_cuota      NUMERIC(12, 2),
    lista_simple_3_cuotas     NUMERIC(12, 2),
    lista_simple_6_cuotas     NUMERIC(12, 2),
    lista_plan_z              NUMERIC(12, 2),
    lista_naranja_cobro       NUMERIC(12, 2),
    lista_mercadopago_1_cuota NUMERIC(12, 2),
    lista_mercadopago_3_cuotas NUMERIC(12, 2),
    lista_mercadopago_6_cuotas NUMERIC(12, 2),
    lista_mercadopago_2_cuotas NUMERIC(12, 2),
    creado_en       TIMESTAMPTZ DEFAULT NOW(),
    actualizado_en  TIMESTAMPTZ DEFAULT NOW()
);
```

### Índices creados
```sql
CREATE INDEX idx_productos_publicado ON productos (publicado_web) WHERE activo = TRUE;
CREATE INDEX idx_productos_oferta    ON productos (en_oferta)     WHERE activo = TRUE;
CREATE INDEX idx_productos_rubro     ON productos (rubro);
CREATE INDEX idx_productos_nombre    ON productos USING gin(to_tsvector('spanish', nombre));
```

### Estado actual
- **12.289 productos activos** cargados
- RLS **desactivado** — activar antes de producción con políticas adecuadas
- El índice GIN sobre `nombre` habilita full-text search en español

### Campos clave del ERP mapeados
| Campo ERP | Columna DB | Descripción |
|---|---|---|
| `ARCOD` | `codigo` | Código interno |
| `ARCOF` / `ARCOA` | `codigo_alt` | Código alternativo |
| `ARNOM` | `nombre` | Nombre del artículo |
| `ARRUB` | `rubro` | Rubro/categoría |
| `ARMAR` | `marca` | Marca |
| `ARPRV` | `precio_venta` | Precio de venta con IVA |
| `ARPRC` | `costo` | Costo |
| `ARPUB` | `publicado_web` | Flag para publicar en web ⚠️ actualmente todos en False |
| `AROFE` | `en_oferta` | Flag de oferta |

---

## 4. Scripts de sincronización (Python)

Ubicación en producción: carpeta local en la PC del negocio junto a la carpeta `datos/` del ERP.

### Archivos
```
📁 carpeta-produccion/
   exportar_catalogo.py     — snapshot completo del ERP → Excel
   detectar_cambios.py      — compara ERP vs Excel anterior → solo cambios
   sincronizar_db.py        — sube cambios Excel → Supabase via REST
   sincronizar.bat          — launcher Windows (doble clic, encadena los 3)
   .env                     — credenciales Supabase (NO commitear)
   📁 historial/            — snapshots anteriores con fecha
```

### Uso diario (empleado)
```
Doble clic en sincronizar.bat
```
El bat hace automáticamente:
1. Exporta catálogo actual del ERP
2. Compara con el snapshot más reciente en `historial/`
3. Sube solo los cambios a Supabase
4. Guarda el nuevo snapshot en `historial/`

### Uso manual
```bash
# Exportar todo
python exportar_catalogo.py --datos "C:\a\datos"

# Solo publicados en web
python exportar_catalogo.py --datos "C:\a\datos" --solo-publicados

# Solo con stock
python exportar_catalogo.py --datos "C:\a\datos" --solo-con-stock

# Detectar cambios
python detectar_cambios.py --datos "C:\a\datos" --anterior historial/catalogo_anterior.xlsx

# Carga inicial Supabase
python sincronizar_db.py --inicial catalogo_inicial.xlsx

# Sincronizar cambios
python sincronizar_db.py --cambios cambios_YYYYMMDD.xlsx

# Dry-run (simula sin tocar DB)
python sincronizar_db.py --cambios cambios.xlsx --dry-run

# Ver SQL de creación de tabla
python sincronizar_db.py --mostrar-sql
```

### Dependencias Python
```bash
python -m pip install dbfread openpyxl requests python-dotenv
```

### .env requerido
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=service_role_key   ← service_role, NO la anon key
```

---

## 5. Panel Admin (sprint actual)

### Estado
Existe un `admin.html` funcional (HTML/JS vanilla, sin framework).
Decisión tomada: **migrar a Next.js** para modularizar y preparar el e-commerce.

### Funcionalidades implementadas en admin.html
- Login con Supabase Auth (email + password)
- Configuración inicial de credenciales (guardada en localStorage)
- Tabla de productos con paginación (50 por página)
- Búsqueda por texto, filtros por publicado/oferta/stock
- Toggle publicado_web y en_oferta por artículo
- Acciones masivas sobre selección múltiple
- Stats en tiempo real (total, publicados, ofertas, con stock)

### Bug conocido a corregir en Next
La búsqueda actual carga solo 1000 productos (límite default Supabase REST).
**Solución definida: búsqueda server-side** con `ilike` y full-text search (`fts`)
contra Supabase, paginación de 50 resultados por query. NO cargar todo en el browser.

---

## 6. Estructura Next.js propuesta

```
electricidad-app/
├── app/
│   ├── (admin)/
│   │   ├── layout.tsx       ← auth guard, solo usuarios logueados
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── productos/
│   │       └── page.tsx     ← tabla con server-side search
│   ├── (store)/             ← reservado para e-commerce (sprint 3)
│   │   └── .gitkeep
│   └── layout.tsx
├── lib/
│   └── supabase/
│       ├── client.ts        ← browser client (anon key)
│       └── server.ts        ← server client (service_role, solo server)
├── components/
│   ├── admin/
│   └── store/               ← reservado
└── types/
    └── producto.ts
```

### Comando de creación
```bash
npx create-next-app@latest electricidad-app \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir
```

### Dependencias a instalar
```bash
npm install @supabase/supabase-js @supabase/ssr
```

---

## 7. Decisiones pendientes

| Decisión | Opciones | Prioridad |
|---|---|---|
| Backend API | Supabase directo vs NestJS | Baja — decidir al llegar al portal del cliente |
| Dominio/deployment | Mismo dominio rutas separadas vs subdominios | Baja |
| RLS policies | Diseñar antes de producción | Alta |
| ARPUB adoption | El negocio debe empezar a marcar artículos | Crítica — sin esto el catálogo web está vacío |

---

## 8. Próximo sprint (Sprint 2 — Panel Admin en Next.js)

### Objetivo
Reemplazar `admin.html` con la misma funcionalidad en Next.js,
corrigiendo el bug de búsqueda y dejando la estructura lista para el e-commerce.

### Tareas en orden
1. Crear proyecto Next.js con estructura definida
2. Configurar Supabase client (browser + server)
3. Implementar autenticación con `@supabase/ssr`
4. Página `/admin/productos` con búsqueda server-side
5. Toggles publicado/oferta con optimistic UI
6. Acciones masivas
7. Dashboard de stats

### Criterio de éxito
Búsqueda sobre los 12.289 productos funciona correctamente,
el empleado puede marcar artículos como publicados desde el browser.

---

## 9. Sprint 3 (futuro) — Portal del cliente / E-commerce

### Funcionalidades planificadas
- Catálogo público (solo `publicado_web = true`)
- Filtros por rubro, marca, oferta
- Tipos de cliente: retail (lista_normal) y mayorista/gremio (otras listas)
- Self-service de presupuestos: cargar artículos, generar PDF, workflow de aprobación
- Conversión de presupuesto aprobado a orden de compra con link de pago

### Pendiente de diseño
- UX del flujo del cliente (no diseñado aún)
- Autenticación de clientes (separada de la auth de admin)
- Integración de pagos

---

## 10. Notas técnicas importantes

- **ERP es solo lectura** — nunca escribir en los DBF
- **service_role key** solo en scripts Python locales y server-side de Next. Nunca en el browser
- **anon key** en el browser — cuando RLS esté activo, controlará qué puede leer/escribir
- **ARPUB** actualmente todos en `false` en el ERP — el negocio debe activar artículos manualmente desde el software de gestión antes de que aparezcan en la web
- **Listas de precio** son recargos porcentuales sobre `precio_venta`, ya calculados y guardados en la DB
- **Búsqueda full-text**: índice GIN en `nombre` con `to_tsvector('spanish', nombre)` — usar `fts` operator de Supabase o query Postgres directa
