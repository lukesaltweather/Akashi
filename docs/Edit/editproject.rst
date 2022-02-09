======================================================================
editproject
======================================================================
------------------------------------------------------------
Aliases: editproj, editp, ep
------------------------------------------------------------
Description
==============
Edit a project's attributes.

Required Role
=====================
Role `Akashi's Minions`.

Arguments
===========

Required
---------
:project:
    | The project to edit. [:doc:`/Types/project`]

Optional
------------
:title:
    | The title of the project. [:doc:`/Types/text`]
:link:
    | Link to the project on box. [:doc:`/Types/text`]
:thumbnail:
    | Large picture for the entry in the status board. [:doc:`/Types/text`]
:icon:
    | Small Image for the status board in the upper left corner. [:doc:`/Types/text`]
:ts, rd, pr, tl:
    | Default staff for the project. Enter "none" to set the staff to none at all. [:doc:`/Types/staff`]
:status:
    | Current status of the project, defaults to "active". [:doc:`/Types/literals`]
:altnames:
    | Aliases for the project, divided by comma. [:doc:`/Types/text`]
:color:
    | The color the project's embed has in the info board. Can be a hex or one of these colors: [:doc:`/Types/color`]
:position:
    | Where the embed of the project appears in the info board. [:doc:`/Types/number`]