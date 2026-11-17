-- ============================================================================
-- F1 · Catálogo web: subcategoría e imagen por producto
-- ----------------------------------------------------------------------------
-- * subcategoria_web: segundo nivel de navegación (p. ej. Iluminación → Apliques).
-- * imagen_url: foto del producto. Por ahora la URL del sitio del fabricante;
--   más adelante se copian a almacenamiento propio (R2) y se reemplaza la URL.
-- La vista pública suma las dos columnas AL FINAL (requisito de
-- `create or replace view`).
--
-- Idempotente: se puede correr más de una vez.
-- ============================================================================

alter table public.catalogo_web add column if not exists subcategoria_web text;
alter table public.catalogo_web add column if not exists imagen_url text;

alter table public.catalogo_web drop constraint if exists catalogo_web_imagen_https;
alter table public.catalogo_web add constraint catalogo_web_imagen_https
  check (imagen_url is null or imagen_url ~ '^https://');

create index if not exists idx_catalogo_web_cat_sub
  on public.catalogo_web (categoria_web, subcategoria_web) where publicado;

create or replace view public.catalogo_publico
with (security_invoker = false)
as
select
  p.codigo,
  nullif(trim(p.codigo_alt), '')                         as codigo_fabrica,
  coalesce(nullif(trim(c.nombre_web), ''), p.nombre)     as nombre,
  p.marca,
  p.rubro,
  c.categoria_web,
  c.descripcion,
  c.destacado,
  c.orden,
  (coalesce(p.stock, 0) >= cfg.stock_minimo_disp)        as disponible,
  case when cfg.mostrar_precios and p.precio_venta > 0
       then round(p.precio_venta * cfg.factor_precio / cfg.redondeo_precio) * cfg.redondeo_precio
  end                                                    as precio_un_pago,
  c.subcategoria_web,
  c.imagen_url
from public.catalogo_web c
join public.productos p on p.codigo = c.codigo
cross join public.config_web cfg
where c.publicado
  and p.activo;

revoke all on table public.catalogo_publico from anon, authenticated;
grant select on table public.catalogo_publico to anon, authenticated;

comment on view public.catalogo_publico is
  'Única lectura pública del catálogo. Sin costo, precio base, listas ni stock numérico. Ver migraciones 20261113000002 y 20261118000003.';
