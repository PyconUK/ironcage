from django.core.management import BaseCommand
from django.template.loader import get_template

from ...models import Proposal


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('track', nargs='?', choices=['all', 'education', 'pydata'], default='all')

    def handle(self, *args, track, **kwargs):
        if track == 'all':
            proposals = Proposal.objects.all()
        elif track == 'education':
            proposals = Proposal.objects.filter(aimed_at_teachers=True)
        elif track == 'pydata':
            proposals = Proposal.objects.filter(aimed_at_data_scientists=True)
        else:
            assert False

        template = get_template('cfp/_proposal_details.html')

        print('<!DOCTYPE html>')
        print('<html>')
        print('<body>')

        for proposal in proposals:
            print(template.render({'proposal': proposal}))
            print('<hr />')

        print('</body>')
        print('</html>')
