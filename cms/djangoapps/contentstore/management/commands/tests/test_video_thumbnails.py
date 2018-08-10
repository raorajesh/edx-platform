# -*- coding: utf-8 -*-
"""
Tests for course video thumbnails management command.
"""
import logging
from mock import patch
from django.core.management import call_command, CommandError
from django.test import TestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.djangoapps.video_config.models import VideoThumbnailSetting, UpdatedCourseVideos
from six import text_type
from testfixtures import LogCapture

LOGGER_NAME = "contentstore.management.commands.video_thumbnails"


def setup_video_thumbnails_config(batch_size=10, commit=False, all_course_videos=False, course_ids=''):
    VideoThumbnailSetting.objects.create(
        batch_size=batch_size, commit=commit, course_ids=course_ids, all_course_videos=all_course_videos
    )


class TestArgParsing(TestCase):
    """
    Tests for parsing arguments for the `migrate_transcripts` management command
    """
    def test_no_args(self):
        errstring = "Error: argument --from-settings/--from_settings is required"
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('video_thumbnails')

    def test_invalid_course(self):
        errstring = "Invalid key specified: <class 'opaque_keys.edx.locator.CourseLocator'>: invalid-course"
        setup_video_thumbnails_config(course_ids='invalid-course')
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('video_thumbnails', '--from-settings')


class TestVideoThumbnails(ModuleStoreTestCase):
    """
    Tests adding thumbnails to course videos from YouTube
    """
    def setUp(self):
        """ Common setup. """
        super(TestVideoThumbnails, self).setUp()
        self.course = CourseFactory.create()
        self.course_2 = CourseFactory.create()

    @patch('contentstore.management.commands.video_thumbnails.get_course_video_ids_with_youtube_profile')
    def test_video_thumbnails_call_count_without_commit(self, mock_course_videos):
        """
        Test without commit.
        """
        course_videos = [
            (self.course.id, 'super-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP80'),
            (self.course_2.id, 'medium-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP81')
        ]
        mock_course_videos.return_value = course_videos

        setup_video_thumbnails_config(all_course_videos=True)

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            call_command('video_thumbnails', '--from-settings')
            # Verify that list of course video ids is logged.
            logger.check(
                (
                    LOGGER_NAME, 'INFO',
                    ('[Video Thumbnails] Videos(total): 2, '
                    'Videos(updated): 0, Videos(non-updated): 2, '
                    'Videos(update-in-process): 2')
                ),
                (
                    LOGGER_NAME, 'INFO',
                    '[Video Thumbnails] Selected Course Videos: {course_videos} '.format(
                        course_videos=text_type(course_videos)
                    )
                )
            )

    @patch('contentstore.management.commands.video_thumbnails.get_course_video_ids_with_youtube_profile')
    def test_video_thumbnails_call_count_with_commit(self, mock_course_videos):
        """
        Test updating thumbnails with commit
        """
        course_videos = [
            (self.course.id, 'super-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP80'),
            (self.course_2.id, 'medium-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP81')
        ]
        mock_course_videos.return_value = course_videos
        setup_video_thumbnails_config(commit=True, all_course_videos=True)
        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            call_command('video_thumbnails', '--from-settings')
            # Verify that command information correctly logged.
            logger.check(
                (
                    LOGGER_NAME, 'INFO',
                    ('[Video Thumbnails] Videos(total): 2, '
                    'Videos(updated): 0, Videos(non-updated): 2, '
                    'Videos(update-in-process): 2')
                )
            )
