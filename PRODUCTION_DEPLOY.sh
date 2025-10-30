#!/bin/bash
# 🚀 Production Deployment Script for lazysoft.pl
# Branch: claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt
# Date: 2025-10-30

set -e  # Exit on error

echo "🚀 Starting LAZYSOFT Production Deployment..."
echo "================================================"

# Navigate to project directory
cd /opt/lazysoft || exit 1
echo "✅ Changed to /opt/lazysoft"

# Fetch latest changes
echo ""
echo "📥 Fetching latest changes from Git..."
git fetch origin
git checkout claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt
git pull origin claude/fix-newscategory-migrations-011CUdgW3VWKspXwY1DYaVEt
echo "✅ Git changes pulled"

# Stop containers
echo ""
echo "🛑 Stopping containers..."
docker compose -f docker-compose.prod.yml down
echo "✅ Containers stopped"

# Build containers
echo ""
echo "🔨 Building containers (no cache)..."
docker compose -f docker-compose.prod.yml build --no-cache web celery
echo "✅ Containers built"

# Start containers
echo ""
echo "🚀 Starting containers..."
docker compose -f docker-compose.prod.yml up -d
echo "✅ Containers started"

# Wait for containers to be ready
echo ""
echo "⏳ Waiting 15 seconds for containers to initialize..."
sleep 15

# Install pydyf for PDF generation
echo ""
echo "📦 Installing pydyf for PDF generation..."
docker compose -f docker-compose.prod.yml exec -T web pip install --no-cache-dir "pydyf==0.10.0"
echo "✅ pydyf installed"

# Restart web after pip install
echo ""
echo "🔄 Restarting web container..."
docker compose -f docker-compose.prod.yml restart web
echo "✅ Web container restarted"

# Wait after restart
echo ""
echo "⏳ Waiting 10 seconds after restart..."
sleep 10

# Fake-apply hr migration (column already exists)
echo ""
echo "🔧 Fixing hr migration conflict (fake-apply)..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate hr 0005_contract_contract_number_employee_id_number_and_more --fake || {
    echo "⚠️  Warning: hr migration fake-apply failed (might be already applied)"
}
echo "✅ hr migration fixed"

# Apply all migrations
echo ""
echo "📊 Applying all migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate
echo "✅ Migrations applied"

# Check for unapplied migrations
echo ""
echo "🔍 Checking for unapplied migrations..."
UNAPPLIED=$(docker compose -f docker-compose.prod.yml exec -T web python manage.py showmigrations | grep "\[ \]" || true)
if [ -z "$UNAPPLIED" ]; then
    echo "✅ All migrations applied successfully"
else
    echo "⚠️  Warning: Some migrations are still unapplied:"
    echo "$UNAPPLIED"
fi

# Show container status
echo ""
echo "📊 Container status:"
docker compose -f docker-compose.prod.yml ps

# Show recent logs
echo ""
echo "📋 Recent logs (last 50 lines):"
docker compose -f docker-compose.prod.yml logs --tail=50 web celery

echo ""
echo "================================================"
echo "✅ Deployment completed!"
echo ""
echo "🔍 Next steps:"
echo "1. Monitor logs: docker compose -f docker-compose.prod.yml logs -f web celery"
echo "2. Check site: curl -I https://lazysoft.pl"
echo "3. Wait 15 min and check security.log for Google Bot: grep 'fake_bot' /opt/lazysoft/logs/security.log | tail -20"
echo ""
echo "📚 For troubleshooting, see: DEPLOY_INSTRUCTIONS_DOCKER_V2.md"
echo "================================================"
