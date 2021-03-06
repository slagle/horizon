# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack LLC
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.core.urlresolvers import reverse
from django import http

from mox import IsA

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse('horizon:project:images_and_snapshots:index')


class ImagesAndSnapshotsTests(test.TestCase):
    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.cinder: ('volume_snapshot_list', 'volume_get')})
    def test_index(self):
        images = self.images.list()
        snapshots = self.snapshots.list()
        volumes = self.volumes.list()

        for volume in volumes:
            volume.volume_id = volume.id
        for volume in volumes:
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id) \
                          .AndReturn(volume)
        for volume in volumes:
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id) \
                          .AndReturn(volume)
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id)

        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
                                .AndReturn(volumes)
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None).AndReturn([images, False])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/images_and_snapshots/index.html')
        self.assertIn('images_table', res.context)
        images_table = res.context['images_table']
        images = images_table.data
        filter_func = lambda im: im.container_format not in ['aki', 'ari']
        filtered_images = filter(filter_func, images)
        self.assertItemsEqual(images, filtered_images)

        self.assertTrue(len(images), 3)
        row_actions = images_table.get_row_actions(images[0])
        self.assertTrue(len(row_actions), 3)
        row_actions = images_table.get_row_actions(images[1])
        self.assertTrue(len(row_actions), 2)
        self.assertTrue('delete_image' not in
                [a.name for a in row_actions])
        row_actions = images_table.get_row_actions(images[2])
        self.assertTrue(len(row_actions), 3)

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.cinder: ('volume_snapshot_list', 'volume_get')})
    def test_index_no_images(self):
        volumes = self.volumes.list()

        for volume in volumes:
            volume.volume_id = volume.id
        for volume in volumes:
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id) \
                          .AndReturn(volume)
        for volume in volumes:
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id) \
                          .AndReturn(volume)
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id)

        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
                                .AndReturn(volumes)
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None).AndReturn([(), False])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/images_and_snapshots/index.html')

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.cinder: ('volume_snapshot_list', 'volume_get')})
    def test_index_error(self):
        volumes = self.volumes.list()

        for volume in volumes:
            volume.volume_id = volume.id
        for volume in volumes:
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id) \
                          .AndReturn(volume)
        for volume in volumes:
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id) \
                          .AndReturn(volume)
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id)

        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
                                .AndReturn(volumes)
        api.glance.image_list_detailed(IsA(http.HttpRequest),
                                       marker=None) \
                                .AndRaise(self.exceptions.glance)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/images_and_snapshots/index.html')

    @test.create_stubs({api.glance: ('image_list_detailed',),
                        api.cinder: ('volume_snapshot_list', 'volume_get')})
    def test_snapshot_actions(self):
        snapshots = self.snapshots.list()
        volumes = self.volumes.list()

        for volume in volumes:
            volume.volume_id = volume.id
        for volume in volumes:
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id) \
                          .AndReturn(volume)
        for volume in volumes:
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id) \
                          .AndReturn(volume)
            api.cinder.volume_get(IsA(http.HttpRequest), volume.volume_id)

        api.cinder.volume_snapshot_list(IsA(http.HttpRequest)) \
            .AndReturn(volumes)
        api.glance.image_list_detailed(IsA(http.HttpRequest), marker=None) \
            .AndReturn([snapshots, False])
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'project/images_and_snapshots/index.html')
        self.assertIn('images_table', res.context)
        snaps = res.context['images_table']
        self.assertEqual(len(snaps.get_rows()), 3)

        row_actions = snaps.get_row_actions(snaps.data[0])

        # first instance - status active, owned
        self.assertEqual(len(row_actions), 4)
        self.assertEqual(row_actions[0].verbose_name, u"Launch")
        self.assertEqual(row_actions[1].verbose_name, u"Create Volume")
        self.assertEqual(row_actions[2].verbose_name, u"Edit")
        self.assertEqual(row_actions[3].verbose_name, u"Delete Image")

        row_actions = snaps.get_row_actions(snaps.data[1])

        # second instance - status active, not owned
        self.assertEqual(len(row_actions), 2)
        self.assertEqual(row_actions[0].verbose_name, u"Launch")
        self.assertEqual(row_actions[1].verbose_name, u"Create Volume")

        row_actions = snaps.get_row_actions(snaps.data[2])
        # third instance - status queued, only delete is available
        self.assertEqual(len(row_actions), 1)
        self.assertEqual(unicode(row_actions[0].verbose_name),
                         u"Delete Image")
        self.assertEqual(str(row_actions[0]), "<DeleteImage: delete>")
