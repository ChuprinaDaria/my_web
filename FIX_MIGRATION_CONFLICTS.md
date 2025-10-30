# 🔧 Fix Migration Conflicts

## Problem
```
django.db.utils.ProgrammingError: column "contract_number" of relation "hr_contract" already exists
```

The column exists in the database but Django thinks it needs to create it.

---

## Solution: Fake-apply the migration

### Step 1: Check which migrations are unapplied
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations hr
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations rag
```

### Step 2: Fake-apply the problematic hr migration
```bash
# Since the column already exists, mark the migration as applied without running it
docker compose -f docker-compose.prod.yml exec web python manage.py migrate hr 0005_contract_contract_number_employee_id_number_and_more --fake
```

### Step 3: Apply remaining migrations normally
```bash
# Now apply all remaining migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate hr
docker compose -f docker-compose.prod.yml exec web python manage.py migrate rag
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

---

## Quick Fix (all commands together)

```bash
cd /opt/lazysoft

# Fake-apply the problematic migration
docker compose -f docker-compose.prod.yml exec web python manage.py migrate hr 0005_contract_contract_number_employee_id_number_and_more --fake

# Apply all other migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Verify no unapplied migrations remain
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations | grep "\[ \]"
```

---

## Alternative: Check if column exists first

If you want to be extra careful:

```bash
# Check database schema
docker compose -f docker-compose.prod.yml exec db psql -U lazysoft_user -d lazysoft_db -c "\d hr_contract"

# Look for contract_number column in the output
# If it exists, use --fake
# If it doesn't exist, apply normally
```

---

## After Fix: Verify Everything

```bash
# 1. Check no unapplied migrations
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations | grep "\[ \]"

# 2. Check logs for errors
docker compose -f docker-compose.prod.yml logs --tail=50 web celery

# 3. Test the site
curl -I https://lazysoft.pl
```

---

**Created**: 2025-10-30
**Issue**: Migration conflict - column already exists
**Solution**: Fake-apply conflicting migration, then apply rest normally
