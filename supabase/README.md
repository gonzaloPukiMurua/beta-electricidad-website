# Base de datos (Supabase)

Las migraciones de `migrations/` son el esquema vigente. Se aplican **en orden** desde el SQL Editor de Supabase (o con la CLI de Supabase si se instala más adelante). Todas son idempotentes: se pueden volver a correr sin romper nada.

| Migración | Qué hace |
|---|---|
| `20261113000001_cerrar_productos.sql` | Activa RLS en `productos` y quita el acceso a la clave pública. La sincronización (service_role) sigue igual. |
| `20261113000002_catalogo_web.sql` | Crea `admins`, `catalogo_web` (curaduría), `config_web` (interruptor de precios, apagado) y la vista `catalogo_publico`, la única lectura del sitio. |

## Después de aplicar

```bash
python verificar_acceso_publico.py          # debe decir TODO OK (salvo vista vacía)
python cargar_seleccion_catalogo.py --dry-run
python cargar_seleccion_catalogo.py         # publica la selección curada
python verificar_acceso_publico.py          # ahora la vista tiene filas
```

## Reglas

* La clave pública (`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`) **solo** puede leer `catalogo_publico`.
* La `service_role` key vive en `.env` (scripts locales) y en el servidor; nunca en el navegador ni en el repo. **Este repo es público.**
* No agregar a `catalogo_publico` columnas con costo, precio base, listas de precio ni stock numérico.
* La curaduría (`catalogo_web`) no la toca la sincronización del ERP.

## Administradores

Un administrador es un usuario de Supabase Auth cuyo id está en `admins`. Para agregar uno:

1. Supabase → Authentication → Users → **Add user → Create new user** (con "Auto Confirm User").
2. SQL Editor:
   ```sql
   insert into public.admins (user_id, nombre)
   select id, 'Nombre' from auth.users where email = 'correo@ejemplo.com';
   ```
Para quitarlo: `delete from public.admins where nombre = 'Nombre';` (el usuario sigue existiendo, pero ya no puede curar el catálogo).

El registro público de usuarios debe estar **deshabilitado** (Authentication → Sign In / Providers → "Allow new users to sign up" apagado): los administradores se crean a mano.

## Respaldos

El plan gratis de Supabase no incluye respaldos. `respaldar_supabase.py` guarda `catalogo_web`, `config_web`, `admins` y `productos` en `respaldos/` (fuera del repo: tiene costos). `sincronizar.bat` lo corre una vez por semana y se conservan los últimos 12.

```bash
python respaldar_supabase.py                                   # respaldo ahora
python respaldar_supabase.py --restaurar respaldos/respaldo_X.json.gz --tabla catalogo_web --dry-run
python respaldar_supabase.py --restaurar respaldos/respaldo_X.json.gz --tabla catalogo_web
```
`productos` no se restaura: se regenera con la sincronización del ERP. El esquema se recrea corriendo las migraciones.
