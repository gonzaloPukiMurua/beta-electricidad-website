-- ============================================================================
-- F0 · REQ-010 — Cerrar la tabla `productos` al público
-- ----------------------------------------------------------------------------
-- Problema (verificado el 2026-11-13): con la clave pública (anon/publishable)
-- se podían leer las 12.089 filas de `productos`, incluidas `costo`, el precio
-- base y las listas de gremio. Esa clave viaja al navegador.
--
-- Después de esta migración:
--   * anon y authenticated NO leen ni escriben `productos` directamente.
--   * La sincronización del ERP usa la service_role key, que ignora RLS:
--     sigue funcionando sin cambios.
--   * El catálogo público lee solo la vista `catalogo_publico` (migración 2).
--
-- Idempotente: se puede correr más de una vez.
-- ============================================================================

alter table public.productos enable row level security;

-- Sin políticas para anon/authenticated = ninguna fila visible.
-- Además se quitan los permisos de tabla, por si alguien agrega una política
-- permisiva por error más adelante.
revoke all on table public.productos from anon, authenticated;

-- Si existiera alguna política creada a mano desde el panel, se elimina.
do $$
declare p record;
begin
  for p in select policyname from pg_policies
           where schemaname = 'public' and tablename = 'productos'
  loop
    execute format('drop policy %I on public.productos', p.policyname);
  end loop;
end $$;
