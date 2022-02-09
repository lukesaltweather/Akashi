======================================================================
addproject
======================================================================
------------------------------------------------------------
Aliases: ap, addp, addproj
------------------------------------------------------------
Description
==============
Add a project to the database.

Required Role
=====================
Role `Akashi's Minions`.

Arguments
===========
Required
---------
:title:
    | Title of the Project. [:doc:`/Types/text`]
:link:
    | Link to the project on box. [:doc:`/Types/text`]
:thumbnail:
    | Link to large picture for the entry in the status board.  [:doc:`/Types/text`]

Optional
------------
:icon:
    | Link to small Image for the status board in the upper left corner.  [:doc:`/Types/text`]
:ts, rd, pr, tl:
    | Default staff for the project.  [:doc:`/Types/staff`]
:status:
    | Current status of the project, defaults to "active".  [:doc:`/Types/text `]
:altnames:
    | Aliases for the project, divided by comma.  [:doc:`/Types/text`]