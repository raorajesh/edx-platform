# -*- coding: utf-8 -*-
"""
Tests for course video thumbnails management command.
"""

from mock import patch
from django.test import TestCase
from django.core.management import call_command, CommandError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.video_config.models import VideoThumbnailSetting, UpdatedCourseVideos

LOGGER_NAME = "cms.djangoapps.contentstore.tasks"


class TestArgParsing(TestCase):
    """
    Tests for parsing arguments for the `migrate_transcripts` management command
    """
    def test_no_args(self):
        errstring = "Error: argument --from-settings/--from_settings is required"
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('video_thumbnails')



class TestVideoThumbnails(ModuleStoreTestCase):
    """
    Tests adding thumbnails to course videos from YouTube
    """
    def setUp(self):
        """ Common setup. """
        super(TestVideoThumbnails, self).setUp()
        VideoThumbnailSetting.objects.create(
            batch_size=10, commit=True, all_course_videos=True
        )

    def test_video_thumbnails_call_count_with_commit(self):
        """
        Test updating thumbnails with commit
        """
        course_videos = [
            ('test-course1', 'super-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP80'),
            ('test-course2', 'medium-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP81')
        ]
        with patch('edxval.api.get_course_video_ids_with_youtube_profile', return_value=course_videos):
            with patch('cms.djangoapps.contentstore.tasks.enqueue_update_thumbnail_tasks') as tasks:
                call_command('video_thumbnails', '--from-settings')
                self.assertEquals(tasks.called, True, msg='method should be called')
                self.assertEquals(tasks.call_count, 1)
