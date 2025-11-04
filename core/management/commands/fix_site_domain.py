from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Fix site domain from example.com to lazysoft.pl'

    def handle(self, *args, **options):
        try:
            # Отримуємо сайт з ID=1
            site = Site.objects.get(pk=1)

            old_domain = site.domain
            old_name = site.name

            # Оновлюємо домен і назву
            site.domain = 'lazysoft.pl'
            site.name = 'LAZYSOFT'
            site.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated site:\n'
                    f'  Old: {old_domain} ({old_name})\n'
                    f'  New: {site.domain} ({site.name})'
                )
            )

        except Site.DoesNotExist:
            # Якщо сайту не існує, створюємо новий
            site = Site.objects.create(
                id=1,
                domain='lazysoft.pl',
                name='LAZYSOFT'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created new site: {site.domain} ({site.name})'
                )
            )
