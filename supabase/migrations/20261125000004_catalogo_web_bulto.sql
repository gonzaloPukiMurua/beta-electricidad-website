-- ============================================================================
-- F1 · Unidad de venta por bulto
-- ----------------------------------------------------------------------------
-- Algunos artículos tienen precio por metro en el ERP pero se venden por bulto
-- no fraccionable: caño rígido por varilla de 3 m, corrugado por rollo de 25 m.
--
-- * venta_bulto:    nombre del bulto ("varilla", "rollo", "caja").
-- * venta_cantidad: unidades del ERP que trae un bulto (3, 25, 100).
-- * venta_unidad:   unidad del ERP ("m", "u").
--
-- La web muestra "Se vende por varilla de 3 m" y la lista para presupuestar
-- pide bultos y manda la cantidad en unidades del ERP (2 varillas → 6 m).
-- La vista pública suma las columnas AL FINAL (requisito de
-- `create or replace view`).
--
-- Idempotente: se puede correr más de una vez.
-- ============================================================================

alter table public.catalogo_web add column if not exists venta_bulto text;
alter table public.catalogo_web add column if not exists venta_cantidad numeric;
alter table public.catalogo_web add column if not exists venta_unidad text;

alter table public.catalogo_web drop constraint if exists catalogo_web_venta_bulto;
alter table public.catalogo_web add constraint catalogo_web_venta_bulto
  check (venta_bulto is null or (venta_cantidad is not null and venta_cantidad > 0));

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
  c.imagen_url,
  c.venta_bulto,
  c.venta_cantidad,
  c.venta_unidad
from public.catalogo_web c
join public.productos p on p.codigo = c.codigo
cross join public.config_web cfg
where c.publicado
  and p.activo;

revoke all on table public.catalogo_publico from anon, authenticated;
grant select on table public.catalogo_publico to anon, authenticated;

comment on view public.catalogo_publico is
  'Única lectura pública del catálogo. Sin costo, precio base, listas ni stock numérico. Ver migraciones 20261113000002, 20261118000003 y 20261125000004.';
