=========
Storage
=========

Resources related to storage.

Volume
----------

The Volume resource represents ZFS pools and UFS volumes.

List resource
+++++++++++++

.. http:get:: /api/v1.0/storage/volume/

   Returns a list of all interfaces.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/storage/volume/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "status": "HEALTHY",
                "vol_guid": "8443409799014097611",
                "vol_fstype": "ZFS",
                "used": "192.0 KiB (0%)",
                "name": "tank",
                "used_pct": "0%",
                "used_si": "192.0 KiB",
                "id": 1,
                "vol_encryptkey": "",
                "vol_name": "tank",
                "is_decrypted": true,
                "avail_si": "4.9 GiB",
                "mountpoint": "/mnt/tank",
                "vol_encrypt": 0,
                "children": [],
                "total_si": "4.9 GiB"
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/storage/volume/

   Creates a new volume and returns the new volume object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/volume/ HTTP/1.1
      Content-Type: application/json

        {
                "volume_name": "tank",
                "layout": [
                        {
                                "vdevtype": "stripe",
                                "disks": ["ada1", "ada2"]
                        }
                ]
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "status": "HEALTHY",
                "vol_guid": "8443409799014097611",
                "vol_fstype": "ZFS",
                "used": "192.0 KiB (0%)",
                "name": "tank",
                "used_pct": "0%",
                "used_si": "192.0 KiB",
                "id": 1,
                "vol_encryptkey": "",
                "vol_name": "tank",
                "is_decrypted": true,
                "avail_si": "4.9 GiB",
                "mountpoint": "/mnt/tank",
                "vol_encrypt": 0,
                "children": [],
                "total_si": "4.9 GiB"
        }

   :json string volume_name: name of the volume
   :json list layout: list of vdevs composed of "vdevtype" (stripe, mirror, raidz, raidz2, raidz3) and disks (list of disk names)
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/storage/volume/(int:id)/

   Delete volume `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/storage/volume/1/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Scrub
+++++

.. http:post:: /api/v1.0/storage/volume/(int:id|string:name)/scrub/

   Start scrub for volume `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/volume/tank/scrub/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: application/json

      Volume scrub started.

   :resheader Content-Type: content type of the response
   :statuscode 200: no error

.. http:delete:: /api/v1.0/storage/volume/(int:id|string:name)/scrub/

   Stop scrub for volume `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/storage/volume/tank/scrub/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: application/json

      Volume scrub stopped.

   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Replace disk
+++++++++++++

.. http:post:: /api/v1.0/storage/volume/(int:id|string:name)/replace/

   Replace a disk of volume `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/volume/tank/replace/ HTTP/1.1
      Content-Type: application/json

        {
                "label": "gptid/7c4dd4f1-1a1f-11e3-9786-080027c5e4f4",
                "replace_disk": "ada4"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: application/json

      Disk replacement started.

   :json string label: zfs label of the device
   :json string replace_disk: name of the new disk
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Detach disk
+++++++++++++

.. http:post:: /api/v1.0/storage/volume/(int:id|string:name)/detach/

   Detach a disk of volume `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/volume/tank/detach/ HTTP/1.1
      Content-Type: application/json

        {
                "label": "gptid/7c4dd4f1-1a1f-11e3-9786-080027c5e4f4",
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: application/json

      Disk detached.

   :json string label: zfs label of the device
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Unlock
++++++

.. http:post:: /api/v1.0/storage/volume/(int:id|string:name)/unlock/

   Unluck encrypted volume `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/volume/tank/unlock/ HTTP/1.1
      Content-Type: application/json

        {
                "passphrase": "mypassphrase",
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: application/json

      Volume has been unlocked.

   :json string passphrase: passphrase to unlock the volume
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Recovery Key
++++++++++++

.. http:post:: /api/v1.0/storage/volume/(int:id|string:name)/recoverykey/

   Add a recovery key for volume `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/volume/tank/recoverykey/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: application/json

        {
                "message": "New recovery key has been added.",
                "content": "YWRhc2RzYWRhc2RzYWQ="
        }

   :resheader Content-Type: content type of the response
   :statuscode 202: no error

.. http:delete:: /api/v1.0/storage/volume/(int:id|string:name)/recoverykey/

   Remove a recovery key for volume `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/storage/volume/tank/recoverykey/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :resheader Content-Type: content type of the response
   :statuscode 204: no error


Status
++++++

.. http:get:: /api/v1.0/storage/volume/(int:id|string:name)/status/

   Get status of volume `id`.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/storage/volume/tank/status/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "status": "ONLINE",
                "name": "tank",
                "read": "0",
                "id": 1,
                "write": "0",
                "cksum": "0",
                "pk": "tank",
                "type": "root",
                "children": [{
                        "status": "ONLINE",
                        "name": "raidz1-0",
                        "read": "0",
                        "id": 100,
                        "write": "0",
                        "cksum": "0",
                        "type": "vdev",
                        "children": [{
                                "status": "ONLINE",
                                "name": "ada3p2",
                                "read": "0",
                                "label": "gptid/7cc54b3a-1a1f-11e3-9786-080027c5e4f4",
                                "write": "0",
                                "cksum": "0",
                                "id": 101,
                                "type": "dev",
                        },
                        {
                                "status": "ONLINE",
                                "name": "ada2p2",
                                "read": "0",
                                "label": "gptid/7c8bb013-1a1f-11e3-9786-080027c5e4f4",
                                "write": "0",
                                "cksum": "0",
                                "id": 102,
                                "type": "dev",
                        },
                        {
                                "status": "ONLINE",
                                "name": "ada1p2",
                                "read": "0",
                                "label": "gptid/7c4dd4f1-1a1f-11e3-9786-080027c5e4f4",
                                "write": "0",
                                "cksum": "0",
                                "id": 103,
                                "type": "dev",
                        }]
                }]
        }


   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Snapshot
----------

The Snapshot resource represents ZFS snapshots.

List resource
+++++++++++++

.. http:get:: /api/v1.0/storage/snapshot/

   Returns a list of all snapshots.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/storage/snapshot/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
        "filesystem": "tank/jails/.warden-template-pluginjail-9.2-RELEASE-x64",
        "fullname": "tank/jails/.warden-template-pluginjail-9.2-RELEASE-x64@clean",
        "id": "tank/jails/.warden-template-pluginjail-9.2-RELEASE-x64",
        "mostrecent": true,
        "name": "clean",
        "parent_type": "filesystem",
        "refer": "482M",
        "used": "107K"
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/storage/snapshot/

   Creates a new snapshot and returns the new snapshot object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/snapshot/ HTTP/1.1
      Content-Type: application/json

        {
                "dataset": "tank",
                "name": "test"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "filesystem": "tank",
                "fullname": "tank@test",
                "id": "tank",
                "mostrecent": true,
                "name": "test",
                "parent_type": "filesystem",
                "refer": "298K",
                "used": "0"
        }

   :json string dataset: name of dataset to snapshot
   :json string name: name of the snapshot
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/storage/snapshot/(string:id)/

   Delete snapshot `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/storage/snapshot/tank@test/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Task
----------

The Task resource represents Periodic Snapshot Tasks for ZFS Volumes.

List resource
+++++++++++++

.. http:get:: /api/v1.0/storage/task/

   Returns a list of all periodic snapshot tasks.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/storage/task/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "task_ret_count": 2,
                "task_repeat_unit": "weekly",
                "task_enabled": true,
                "task_recursive": false,
                "task_end": "18:00:00",
                "task_interval": 60,
                "task_byweekday": "1,2,3,4,5",
                "task_begin": "09:00:00",
                "task_filesystem": "tank",
                "id": 1,
                "task_ret_unit": "week"
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/storage/task/

   Creates a new Task and returns the new Task object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/task/ HTTP/1.1
      Content-Type: application/json

        {
                "task_filesystem": "tank",
                "task_recursive": false,
                "task_ret_unit": "week",
                "task_interval": 60,
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "task_ret_count": 2,
                "task_repeat_unit": "weekly",
                "task_enabled": true,
                "task_recursive": false,
                "task_end": "18:00:00",
                "task_interval": 60,
                "task_byweekday": "1,2,3,4,5",
                "task_begin": "09:00:00",
                "task_filesystem": "tank",
                "id": 1,
                "task_ret_unit": "week"
        }

   :json string task_repeat_unit: daily, weekly
   :json string task_begin: do not snapshot before
   :json string task_end: do not snapshot after
   :json string task_filesystem: name of the ZFS filesystem
   :json string task_ret_unit: hour, day, week, month, year
   :json string task_byweekday: days of week to snapshot, [1..7]
   :json integer task_interval: how much time has been passed between two snapshot attempts [5, 10, 15, 30, 60, 120, 180, 240, 360, 720, 1440, 10080]
   :json integer task_ret_count: snapshot lifetime value
   :json boolean task_enabled: enabled task
   :json boolean task_recursive: snapshot all children datasets recursively
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/storage/task/(int:id)/

   Update Task `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/storage/task/1/ HTTP/1.1
      Content-Type: application/json

        {
                "task_interval": 30
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "task_ret_count": 2,
                "task_repeat_unit": "weekly",
                "task_enabled": true,
                "task_recursive": false,
                "task_end": "18:00:00",
                "task_interval": 30,
                "task_byweekday": "1,2,3,4,5",
                "task_begin": "09:00:00",
                "task_filesystem": "tank",
                "id": 1,
                "task_ret_unit": "week"
        }

   :json string task_repeat_unit: daily, weekly
   :json string task_begin: do not snapshot before
   :json string task_end: do not snapshot after
   :json string task_filesystem: name of the ZFS filesystem
   :json string task_ret_unit: hour, day, week, month, year
   :json string task_byweekday: days of week to snapshot, [1..7]
   :json integer task_interval: how much time has been passed between two snapshot attempts [5, 10, 15, 30, 60, 120, 180, 240, 360, 720, 1440, 10080]
   :json integer task_ret_count: snapshot lifetime value
   :json boolean task_enabled: enabled task
   :json boolean task_recursive: snapshot all children datasets recursively
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/storage/task/(int:id)/

   Delete Task `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/storage/task/1/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Replication
-----------

The Replication resource represents ZFS Replication tasks.

List resource
+++++++++++++

.. http:get:: /api/v1.0/storage/replication/

   Returns a list of all replications.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/storage/replication/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "repl_end": "23:59:00",
                "repl_remote_dedicateduser": null,
                "repl_userepl": false,
                "repl_limit": 0,
                "repl_remote_port": 22,
                "repl_remote_dedicateduser_enabled": false,
                "repl_begin": "00:00:00",
                "repl_filesystem": "tank",
                "repl_remote_fast_cipher": false,
                "repl_remote_hostkey": "AAAA",
                "repl_enabled": true,
                "repl_resetonce": false,
                "repl_remote_hostname": "testhost",
                "repl_lastsnapshot": "",
                "id": 1,
                "repl_zfs": "tank"
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/storage/replication/

   Creates a new Replication and returns the new Replication object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/replication/ HTTP/1.1
      Content-Type: application/json

        {
                "repl_filesystem": "tank",
                "repl_zfs": "tank",
                "repl_remote_hostname": "testhost",
                "repl_remote_hostkey": "AAAA"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "repl_end": "23:59:00",
                "repl_remote_dedicateduser": null,
                "repl_userepl": false,
                "repl_limit": 0,
                "repl_remote_port": 22,
                "repl_remote_dedicateduser_enabled": false,
                "repl_begin": "00:00:00",
                "repl_filesystem": "tank",
                "repl_remote_fast_cipher": false,
                "repl_remote_hostkey": "AAAA",
                "repl_enabled": true,
                "repl_resetonce": false,
                "repl_remote_hostname": "testhost",
                "repl_lastsnapshot": "",
                "id": 1,
                "repl_zfs": "tank"
        }

   :json boolean repl_enabled: enable replication
   :json string repl_filesystem: filesystem to replicate
   :json string repl_lastsnapshot: last snapshot sent to remote side
   :json string repl_remote_hostname: remote hostname
   :json integer repl_remote_port: remote ssh port
   :json string repl_remote_hostkey: remote ssh publick key
   :json boolean repl_remote_fast_cipher: use fast cipher
   :json boolean repl_remote_dedicateduser_enabled: use dedicated user to replicate
   :json string repl_remote_dedicateduser: dedicated user to replicate
   :json boolean repl_userepl: recursively replicate and remove stale snapshot on remote side
   :json boolean repl_resetonce: initialize remote side for once
   :json integer repl_limit: limit the replication speed in KB/s
   :json string repl_begin: do not start replication before
   :json string repl_end: do not start replication after
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/storage/replication/(int:id)/

   Update Replication `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/storage/replication/1/ HTTP/1.1
      Content-Type: application/json

        {
                "repl_enabled": false
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "repl_end": "23:59:00",
                "repl_remote_dedicateduser": null,
                "repl_userepl": false,
                "repl_limit": 0,
                "repl_remote_port": 22,
                "repl_remote_dedicateduser_enabled": false,
                "repl_begin": "00:00:00",
                "repl_filesystem": "tank",
                "repl_remote_fast_cipher": false,
                "repl_remote_hostkey": "AAAA",
                "repl_enabled": false,
                "repl_resetonce": false,
                "repl_remote_hostname": "testhost",
                "repl_lastsnapshot": "",
                "id": 1,
                "repl_zfs": "tank"
        }

   :json boolean repl_enabled: enable replication
   :json string repl_filesystem: filesystem to replicate
   :json string repl_lastsnapshot: last snapshot sent to remote side
   :json string repl_remote_hostname: remote hostname
   :json integer repl_remote_port: remote ssh port
   :json string repl_remote_hostkey: remote ssh publick key
   :json boolean repl_remote_fast_cipher: use fast cipher
   :json boolean repl_remote_dedicateduser_enabled: use dedicated user to replicate
   :json string repl_remote_dedicateduser: dedicated user to replicate
   :json boolean repl_userepl: recursively replicate and remove stale snapshot on remote side
   :json boolean repl_resetonce: initialize remote side for once
   :json integer repl_limit: limit the replication speed in KB/s
   :json string repl_begin: do not start replication before
   :json string repl_end: do not start replication after
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/storage/replication/(int:id)/

   Delete Replication `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/storage/replication/1/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Scrub
----------

The Scrub resource represents Periodic Snapshot Scrubs for ZFS Volumes.

List resource
+++++++++++++

.. http:get:: /api/v1.0/storage/scrub/

   Returns a list of all scrubs.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/storage/scrub/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "scrub_threshold": 35,
                "scrub_dayweek": "7",
                "scrub_enabled": true,
                "scrub_minute": "00",
                "scrub_hour": "00",
                "scrub_month": "*",
                "scrub_daymonth": "*",
                "scrub_description": "",
                "id": 1,
                "scrub_volume": "tank"
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/storage/scrub/

   Creates a new Scrub and returns the new Scrub object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/storage/scrub/ HTTP/1.1
      Content-Type: application/json

        {
                "scrub_volume": 1,
                "scrub_dayweek": "7",
                "scrub_minute": "00",
                "scrub_hour": "00",
                "scrub_month": "*",
                "scrub_daymonth": "*"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "scrub_threshold": 35,
                "scrub_dayweek": "7",
                "scrub_enabled": true,
                "scrub_minute": "00",
                "scrub_hour": "00",
                "scrub_month": "*",
                "scrub_daymonth": "*",
                "scrub_description": "",
                "id": 1,
                "scrub_volume": "tank"
        }

   :json integer scrub_volume: id to volume object
   :json integer scrub_threshold: determine how many days shall be between scrubs
   :json string scrub_description: user description
   :json string scrub_minute: values 0-59 allowed
   :json string scrub_hour: values 0-23 allowed
   :json string scrub_daymonth: day of month, values 1-31 allowed
   :json string scrub_month: month
   :json string scrub_dayweek: day of week
   :json boolean scrub_enabled: scrub enabled
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/storage/scrub/(int:id)/

   Update Scrub `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/storage/scrub/1/ HTTP/1.1
      Content-Type: application/json

        {
                "scrub_dayweek": "6"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "scrub_threshold": 35,
                "scrub_dayweek": "6",
                "scrub_enabled": true,
                "scrub_minute": "00",
                "scrub_hour": "00",
                "scrub_month": "*",
                "scrub_daymonth": "*",
                "scrub_description": "",
                "id": 1,
                "scrub_volume": "tank"
        }

   :json integer scrub_volume: id to volume object
   :json integer scrub_threshold: determine how many days shall be between scrubs
   :json string scrub_description: user description
   :json string scrub_minute: values 0-59 allowed
   :json string scrub_hour: values 0-23 allowed
   :json string scrub_daymonth: day of month, values 1-31 allowed
   :json string scrub_month: month
   :json string scrub_dayweek: day of week
   :json boolean scrub_enabled: scrub enabled
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/storage/scrub/(int:id)/

   Delete Scrub `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/storage/scrub/1/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Disk
----------

The Disk resource represents available disks in the system.

List resource
+++++++++++++

.. http:get:: /api/v1.0/storage/disk/

   Returns a list of all disks.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/storage/disk/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "disk_acousticlevel": "Disabled",
                "disk_advpowermgmt": "Disabled",
                "disk_serial": "VBad9d9bb7-3d1d3bce",
                "disk_size": "4294967296",
                "disk_multipath_name": "",
                "disk_identifier": "{serial}VBad9d9bb7-3d1d3bce",
                "disk_togglesmart": true,
                "id": 8,
                "disk_hddstandby": "Always On",
                "disk_transfermode": "Auto",
                "disk_multipath_member": "",
                "disk_description": "",
                "disk_smartoptions": "",
                "disk_enabled": true,
                "disk_name": "ada7"
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/storage/disk/(int:id)/

   Update Disk `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/storage/disk/1/ HTTP/1.1
      Content-Type: application/json

        {
                "disk_togglesmart": false
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "disk_acousticlevel": "Disabled",
                "disk_advpowermgmt": "Disabled",
                "disk_serial": "VBad9d9bb7-3d1d3bce",
                "disk_size": "4294967296",
                "disk_multipath_name": "",
                "disk_identifier": "{serial}VBad9d9bb7-3d1d3bce",
                "disk_togglesmart": false,
                "id": 8,
                "disk_hddstandby": "Always On",
                "disk_transfermode": "Auto",
                "disk_multipath_member": "",
                "disk_description": "",
                "disk_smartoptions": "",
                "disk_enabled": true,
                "disk_name": "ada7"
        }

   :json string disk_description: user description
   :json string disk_hddstandby: Always On, 5, 10, 20, 30, 60, 120, 180, 240, 300, 330
   :json string disk_advpowermgmt: Disabled, 1, 64, 127, 128. 192, 254
   :json string disk_acousticlevel: Disabled, Minimum, Medium, Maximum
   :json boolean disk_togglesmart: Enable S.M.A.R.T.
   :json string disk_smartoptions: S.M.A.R.T. extra options
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error
