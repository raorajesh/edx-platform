"""
Command to add thumbnails to videos.
"""

import logging
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from edxval.api import get_course_video_ids_with_youtube_profile
from openedx.core.djangoapps.video_config.models import VideoThumbnailSetting, UpdatedCourseVideos
from cms.djangoapps.contentstore.tasks import enqueue_update_thumbnail_tasks
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from six import text_type

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py cms video_thumbnails --from-settings
    """
    help = 'Adds thumbnails from YouTube to videos'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--from-settings', '--from_settings',
            dest='from_settings',
            help='Update videos with settings set via django admin',
            action='store_true',
            default=False,
            required=True
        )

    def _get_command_options(self):
        """
        Returns the command arguments configured via django admin.
        """
        command_settings = self._latest_settings()
        commit = command_settings.commit
        if command_settings.all_course_videos:

            all_course_video_ids = get_course_video_ids_with_youtube_profile()
            updated_course_videos = UpdatedCourseVideos.objects.all().values_list('course_id', 'edx_video_id')
            non_updated_course_videos = [
                course_video_id
                for course_video_id in all_course_video_ids
                if (course_video_id[0], course_video_id[1]) not in list(updated_course_videos)
            ]
            # Video batch to be updated
            course_video_batch = non_updated_course_videos[:command_settings.batch_size]

            log.info(
                ('[Video Thumbnails] Videos(total): %s, '
                 'Videos(updated): %s, Videos(non-updated): %s, '
                 'Videos(update-in-process): %s'),
                len(all_course_video_ids),
                len(updated_course_videos),
                len(non_updated_course_videos),
                len(course_video_batch),
            )
        else:
            validated_course_strings = self._parse_course_strings(command_settings.course_ids.split())
            course_video_batch = get_course_video_ids_with_youtube_profile(validated_course_strings)

        return course_video_batch, commit

    def _parse_course_strings(self, course_key_strings):
        """
        Parses and validates the list of course key strings.
        """
        try:
            for course_key_string in course_key_strings:
                CourseKey.from_string(course_key_string)
            return course_key_strings
        except InvalidKeyError as error:
            raise CommandError('Invalid key specified: {}'.format(text_type(error)))

    def _latest_settings(self):
        """
        Return the latest version of the VideoThumbnailSetting
        """
        return VideoThumbnailSetting.current()

    def handle(self, *args, **options):
        """
        Invokes the video thumbnail enqueue function.
        """
        command_settings = self._latest_settings()
        course_video_batch, commit = self._get_command_options()
        command_run = command_settings.increment_run() if commit else -1
        if commit:
            enqueue_update_thumbnail_tasks(course_video_ids=course_video_batch)
        else:
            log.info(
                '[Video Thumbnails] Selected Course Videos: {course_videos} '
                .format(course_videos=text_type(course_video_batch))
            )

        if commit and command_settings.all_course_videos:
            UpdatedCourseVideos.objects.bulk_create([
                UpdatedCourseVideos(course_id=course_video_id[0],
                                    edx_video_id=course_video_id[1],
                                    command_run=command_run)
                for course_video_id in course_video_batch
            ])
