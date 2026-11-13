-- ============================================================================
-- F0 · REQ-010, REQ-013 (D-004), REQ-028 (D-008) — Curaduría web separada del ERP
-- ----------------------------------------------------------------------------
-- * `catalogo_web`: lo que decide el negocio (publicado, destacado, nombre y
--   descripción para la web, categoría). La sincronización del ERP NO la toca.
-- * `config_web`: parámetros del sitio (interruptor de precios, factor).
-- * `admins`: usuarios de Supabase Auth que pueden curar el catálogo.
-- * `catalogo_publico`: única puerta de lectura para el sitio. No expone costo,
--   precio base, listas ni stock numérico.
--
-- Idempotente: se puede correr más de una vez.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Administradores
-- ---------------------------------------------------------------------------
create table if not exists public.admins (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  nombre     text,
  creado_en  timestamptz not null default now()
);
alter table public.admins enable row level security;
revoke all on table public.admins from anon, authenticated;

create or replace function public.es_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (select 1 from public.admins a where a.user_id = auth.uid());
$$;
revoke all on function public.es_admin() from public, anon;
grant execute on function public.es_admin() to authenticated;

-- ---------------------------------------------------------------------------
-- Curaduría
-- ---------------------------------------------------------------------------
-- La FK necesita `productos.codigo` único. El DDL original ya lo declara
-- UNIQUE; este índice es una red de seguridad si la tabla se creó distinto.
create unique index if not exists ux_productos_codigo on public.productos (codigo);

create table if not exists public.catalogo_web (
  codigo          integer primary key references public.productos (codigo) on update cascade,
  publicado       boolean not null default false,
  destacado       boolean not null default false,
  categoria_web   text,                -- p. ej. 'Lámparas LED', 'Artefactos', 'Llaves y tomas'
  nombre_web      text,                -- nombre legible; si es null se usa el del ERP
  descripcion     text,
  orden           integer,
  creado_en       timestamptz not null default now(),
  actualizado_en  timestamptz not null default now()
);
create index if not exists idx_catalogo_web_publicado on public.catalogo_web (categoria_web) where publicado;

create or replace function public.set_actualizado_en_cw()
returns trigger language plpgsql set search_path = '' as $$
begin new.actualizado_en = now(); return new; end; $$;

drop trigger if exists trg_catalogo_web_actualizado on public.catalogo_web;
create trigger trg_catalogo_web_actualizado
  before update on public.catalogo_web
  for each row execute function public.set_actualizado_en_cw();

alter table public.catalogo_web enable row level security;
revoke all on table public.catalogo_web from anon;
grant select, insert, update, delete on table public.catalogo_web to authenticated;

drop policy if exists "admins gestionan el catalogo" on public.catalogo_web;
create policy "admins gestionan el catalogo" on public.catalogo_web
  for all to authenticated
  using ((select public.es_admin()))
  with check ((select public.es_admin()));

-- ---------------------------------------------------------------------------
-- Parámetros del sitio
-- ---------------------------------------------------------------------------
create table if not exists public.config_web (
  id                 boolean primary key default true check (id),  -- una sola fila
  mostrar_precios    boolean not null default false,               -- D-008: apagado en la fase 1
  factor_precio      numeric(6,4) not null default 0.7500,         -- sobre el precio base del ERP
  redondeo_precio    integer not null default 10,                  -- redondear a múltiplos de $10
  stock_minimo_disp  numeric(10,2) not null default 1,             -- "Disponible" desde este stock
  actualizado_en     timestamptz not null default now()
);
insert into public.config_web (id) values (true) on conflict (id) do nothing;

alter table public.config_web enable row level security;
revoke all on table public.config_web from anon;
grant select, update on table public.config_web to authenticated;

drop policy if exists "admins leen y editan la config" on public.config_web;
create policy "admins leen y editan la config" on public.config_web
  for all to authenticated
  using ((select public.es_admin()))
  with check ((select public.es_admin()));

-- ---------------------------------------------------------------------------
-- Vista pública
-- ---------------------------------------------------------------------------
-- La vista corre con los permisos de su dueño (security_invoker = false), a
-- propósito: así anon puede leer estas columnas calculadas sin tener acceso a
-- `productos`. El linter de Supabase la marca como "security definer view";
-- es intencional y es la forma de restringir columnas. No agregar columnas
-- sensibles (costo, precio_venta, lista_*, stock numérico).
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
  end                                                    as precio_un_pago
from public.catalogo_web c
join public.productos p on p.codigo = c.codigo
cross join public.config_web cfg
where c.publicado
  and p.activo;

revoke all on table public.catalogo_publico from anon, authenticated;
grant select on table public.catalogo_publico to anon, authenticated;

comment on view public.catalogo_publico is
  'Única lectura pública del catálogo. Sin costo, precio base, listas ni stock numérico. Ver migración 20261113000002.';
