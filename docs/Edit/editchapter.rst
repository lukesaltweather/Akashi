======================================================================
editchapter
======================================================================
------------------------------------------------------------
Aliases: editch, editc, ec
------------------------------------------------------------
Description
==============
Edit a chapters attributes.

Required Role
=====================
Role `Neko Workers`.

Arguments
===========

Required
---------
:chapter: 
    | The chapter to edit, in format: projectName chapterNbr [:doc:`/Types/chapter`]

Optional
------------
:title: 
    | Title of the chapter. [:doc:`/Types/text`]
:tl, rd, ts, pr:
    | Staff for the chapter. [:doc:`/Types/staff`]
:link_tl, link_rd, link_ts, link_pr, link_qcts, link_raw:
    | Links to specific steps of chapter on Box. [:doc:`/Types/text`]
:to_project:
    | Change the project the chapter belongs to. [:doc:`/Types/project`]
:to_chapter:
    | Change the chapter number. [:doc:`/Types/number`]