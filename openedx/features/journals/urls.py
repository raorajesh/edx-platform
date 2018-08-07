"""
Defines URLs for course bookmarks.
"""

from django.conf import settings
from django.conf.urls import url

from openedx.features.journals.views.marketing import bundle_about, render_xblock_by_journal_access
from openedx.features.journals.views import learner_dashboard

urlpatterns = [
    url(r'^bundles/{}/about'.format(r'(?P<bundle_uuid>[0-9a-f-]+)',),
        bundle_about,
        name='openedx.journals.bundle_about'
        ),
    url(r'^$',
        learner_dashboard.journal_listing,
        name='openedx.journals.dashboard'
        ),
    url(r'^check_user_access/{usage_key_string}'.format(usage_key_string=settings.USAGE_KEY_PATTERN),
        render_xblock_by_journal_access,
        name='openedx.journals.render_xblock_by_journal_access'
        ),
]
