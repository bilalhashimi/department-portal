from django.core.management.base import BaseCommand
from documents.vector_service import vector_service


class Command(BaseCommand):
    help = 'Initialize the vector database collection'

    def handle(self, *args, **options):
        self.stdout.write('Initializing vector database...')
        
        try:
            # The vector service automatically ensures collection exists during initialization
            # We can just check if it's working by getting collection stats
            stats = vector_service.get_document_stats()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully initialized vector database collection')
            )
            self.stdout.write(f'Collection stats: {stats}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize vector database: {str(e)}')
            ) 