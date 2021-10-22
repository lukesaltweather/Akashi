==============================
What's new in Akashi 2?
==============================
---------------------
1. Command Format
---------------------
With Akashi 2, the way to write commands changed radically. You might recognize the new format from Discord's search bar.
The new way to do commands looks like this:
.. code-block:: text
    
    $editchapter chapter: yankee 62 title: Yukiko-san is Fine ① ts: lukesaltweather

---------------------
1. Chapter Selection
---------------------
With Akashi 2, chapters are specified in a different manner.
Instead of having 2 arguments for a chapter (chapter and project), the two have now merged into a single argument "chapter".
This works like so:
.. code-block:: text

    $editchapter chapter: yankee 52 ts: lukesaltweather

--------------------
3. Notes
--------------------
Notes were historically not among the features most well treated. This changes with this update:
Several new commands have been introduced to deal with notes, like adding, deleting or editing notes.
For this, the bot now makes use of Discord's new UI Elements.

Displaying notes has also been improved in the file-room messages.
For more info see :doc:`/Note`

---------------------------------------
4. Addition of the *track* feature
---------------------------------------
A new command *track* has been added, which allows users to be updated by dm on updates on their tracked chapters and projects.
With the *track* command, notifications for a specific chapter or project can be enabled.
By using *untrack*, one can disable those notifications.

-------------------------------
5. Changes to done
-------------------------------
TODO

-------------------------------
6. Backups
-------------------------------
Akashi now features a new backup functionality, which publishes a new database dump every hour into the command channel.
This backup can then be used to restore a replacement database to the last backup state, in case things go south.