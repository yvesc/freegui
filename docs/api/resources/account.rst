=========
Account
=========

Resources related to accounts.

Users
----------

The Users resource represents all unix users.

List resource
+++++++++++++

.. http:get:: /api/v1.0/account/users/

   Returns a list of all current users.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/account/users/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "bsdusr_builtin": true,
                "bsdusr_email": "",
                "bsdusr_full_name": "root",
                "bsdusr_group": 0,
                "bsdusr_home": "/root",
                "bsdusr_locked": false,
                "bsdusr_password_disabled": false,
                "bsdusr_shell": "/bin/csh",
                "bsdusr_smbhash": "root:0:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX:E6FCEFB62A365065CE5B5F04AB12B455:[U          ]:LCT-52272D9E:",
                "bsdusr_uid": 0,
                "bsdusr_unixhash": "$6$d8doVGxjhDhL4feI$YpTtmlhCmbc6BJ4MQcBsPvZA0Ge4SMnAyZn9CfZLpkuP71g8bPq6DkKJBmcN61z2oQSj0K8RtaqmKltc9HsMg0",
                "bsdusr_username": "root",
                "bsdusr_sudo": false,
                "id": 1
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/account/users/

   Creates a new user and returns the new user object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/account/users/ HTTP/1.1
      Content-Type: application/json

        {
                "bsdusr_username": "myuser",
                "bsdusr_creategroup": true,
                "bsdusr_full_name": "haha",
                "bsdusr_password": "aa",
                "bsdusr_uid": 1111
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "bsdusr_builtin": false,
                "bsdusr_email": "",
                "bsdusr_full_name": "My User",
                "bsdusr_group": 0,
                "bsdusr_home": "/nonexistent",
                "bsdusr_locked": false,
                "bsdusr_password_disabled": false,
                "bsdusr_shell": "/bin/csh",
                "bsdusr_smbhash": "myuser:0:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX:E6FCEFB62A365065CE5B5F04AB12B455:[U          ]:LCT-52272D9E:",
                "bsdusr_uid": 1111,
                "bsdusr_unixhash": "$6$d8doVGxjhDhL4feI$YpTtmlhCmbc6BJ4MQcBsPvZA0Ge4SMnAyZn9CfZLpkuP71g8bPq6DkKJBmcN61z2oQSj0K8RtaqmKltc9HsMg0",
                "bsdusr_username": "myuser",
                "bsdusr_sudo": false,
                "id": 25
        }

   :json string bsdusr_username: unix username
   :json string bsdusr_full_name: name of the user
   :json string bsdusr_password: password for the user
   :json integer bsdusr_uid: unique user id
   :json integer bsdusr_group: id of the group object
   :json boolean bsdusr_creategroup: create a group for the user
   :json string bsdusr_mode: unix mode to set the homedir
   :json string bsdusr_shell: shell for the user login
   :json boolean bsdusr_password_disabled: disabled password login
   :json boolean bsdusr_locked: lock user login
   :json boolean bsdusr_sudo: enable sudo for the user
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/account/users/(int:id)/

   Creates a new user and returns the new user object.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/account/users/25/ HTTP/1.1
      Content-Type: application/json

        {
                "bsdusr_full_name": "My Name",
                "bsdusr_shell": "/bin/bash",
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "bsdusr_builtin": false,
                "bsdusr_email": "",
                "bsdusr_full_name": "My Name",
                "bsdusr_group": 0,
                "bsdusr_home": "/nonexistent",
                "bsdusr_locked": false,
                "bsdusr_password_disabled": false,
                "bsdusr_shell": "/bin/bash",
                "bsdusr_smbhash": "myuser:0:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX:E6FCEFB62A365065CE5B5F04AB12B455:[U          ]:LCT-52272D9E:",
                "bsdusr_uid": 1111,
                "bsdusr_unixhash": "$6$d8doVGxjhDhL4feI$YpTtmlhCmbc6BJ4MQcBsPvZA0Ge4SMnAyZn9CfZLpkuP71g8bPq6DkKJBmcN61z2oQSj0K8RtaqmKltc9HsMg0",
                "bsdusr_username": "myuser",
                "bsdusr_sudo": false,
                "id": 25
        }

   :json string bsdusr_full_name: name of the user
   :json string bsdusr_password: password for the user
   :json integer bsdusr_uid: unique user id
   :json integer bsdusr_group: id of the group object
   :json string bsdusr_mode: unix mode to set the homedir
   :json string bsdusr_shell: shell for the user login
   :json boolean bsdusr_password_disabled: disabled password login
   :json boolean bsdusr_locked: lock user login
   :json boolean bsdusr_sudo: enable sudo for the user
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/account/users/(int:id)/

   Delete user `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/account/users/25/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error


Change password
+++++++++++++++


.. http:post:: /api/v1.0/account/users/(int:id)/password/

   Change password of user `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/account/users/25/password/ HTTP/1.1
      Content-Type: application/json

        {
                "bsdusr_password": "newpasswd"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json


        {
                "bsdusr_builtin": false,
                "bsdusr_email": "",
                "bsdusr_full_name": "My User",
                "bsdusr_group": 0,
                "bsdusr_home": "/nonexistent",
                "bsdusr_locked": false,
                "bsdusr_password_disabled": false,
                "bsdusr_shell": "/bin/csh",
                "bsdusr_smbhash": "myuser:0:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX:E6FCEFB62A365065CE5B5F04AB12B455:[U          ]:LCT-52272D9E:",
                "bsdusr_uid": 0,
                "bsdusr_unixhash": "$6$d8doVGxjhDhL4feI$YpTtmlhCmbc6BJ4MQcBsPvZA0Ge4SMnAyZn9CfZLpkuP71g8bPq6DkKJBmcN61z2oQSj0K8RtaqmKltc9HsMg0",
                "bsdusr_username": "myuser",
                "bsdusr_sudo": false,
                "id": 25
        }

   :json string bsdusr_password: new password
   :statuscode 200: no error


Get user groups
++++++++++++++++

.. http:get:: /api/v1.0/account/users/(int:id)/groups/

   Get a list of groups of user `id`.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/account/users/25/groups/ HTTP/1.1
      Accept: application/json, text/javascript

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: text/javascript

        []

   :statuscode 200: no error


Set user groups
++++++++++++++++

.. http:post:: /api/v1.0/account/users/(int:id)/groups/

   Set a list of groups of user `id`.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/account/users/25/groups/ HTTP/1.1
      Accept: application/json, text/javascript

        [
                "wheel",
                "ftp"
        ]

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Accepted
      Vary: Accept
      Content-Type: text/javascript

        [
                "wheel",
                "ftp"
        ]

   :statuscode 202: no error


Groups
----------

The Groups resource represents all unix groups.

List resource
+++++++++++++

.. http:get:: /api/v1.0/account/groups/

   Returns a list of all current groups.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1.0/account/groups/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
                "bsdgrp_builtin": False,
                "bsdgrp_gid": 1111,
                "bsdgrp_group": "myuser",
                "bsdgrp_sudo": false,
                "id": 33
        },
        {
                "bsdgrp_builtin": true,
                "bsdgrp_gid": 0,
                "bsdgrp_group": "wheel",
                "bsdgrp_sudo": false,
                "id": 1
        },
        {
                "bsdgrp_builtin": true,
                "bsdgrp_gid": 1,
                "bsdgrp_group": "daemon",
                "bsdgrp_sudo": false,
                "id": 2
        }
      ]

   :query offset: offset number. default is 0
   :query limit: limit number. default is 30
   :resheader Content-Type: content type of the response
   :statuscode 200: no error


Create resource
+++++++++++++++

.. http:post:: /api/v1.0/account/groups/

   Creates a new group and returns the new group object.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1.0/account/groups/ HTTP/1.1
      Content-Type: application/json

        {
                "bsdgrp_gid": 1200,
                "bsdgrp_group": "mygroup"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Vary: Accept
      Content-Type: application/json

        {
                "bsdgrp_builtin": false,
                "bsdgrp_gid": 1200,
                "bsdgrp_group": "mygroup",
                "bsdgrp_sudo": false,
                "id": 34
        }

   :json integer bsdgrp_gid: group unique id
   :json string bsdgrp_group: unix name for the group
   :json boolean bsdgrp_sudo: enable sudo for this group
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 201: no error


Update resource
+++++++++++++++

.. http:put:: /api/v1.0/account/groups/(int:id)/

   Update group `id`.

   **Example request**:

   .. sourcecode:: http

      PUT /api/v1.0/account/groups/34/ HTTP/1.1
      Content-Type: application/json

        {
                "bsdgrp_group": "newgroup"
        }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

        {
                "bsdgrp_builtin": false,
                "bsdgrp_gid": 1200,
                "bsdgrp_group": "newgroup",
                "bsdgrp_sudo": false,
                "id": 34
        }

   :json string bsdgrp_group: unix name for the group
   :json boolean bsdgrp_sudo: enable sudo for this group
   :reqheader Content-Type: the request content type
   :resheader Content-Type: the response content type
   :statuscode 200: no error


Delete resource
+++++++++++++++

.. http:delete:: /api/v1.0/account/groups/(int:id)/

   Delete group `id`.

   **Example request**:

   .. sourcecode:: http

      DELETE /api/v1.0/account/groups/34/ HTTP/1.1
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Response
      Vary: Accept
      Content-Type: application/json

   :statuscode 204: no error
