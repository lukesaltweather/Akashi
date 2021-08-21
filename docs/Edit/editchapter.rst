======================================================================
editchapter
======================================================================
Description
==============
Edit a chapters attributes.

Required Role
=====================
Role `Neko Workers`.

Parameters
===========
Required
---------
:chapter: The chapter to edit, in format: projectName chapterNbr
Optional
------------
:title: Title of the chapter.
:tl, rd, ts, pr: Staff for the chapter.
:link_tl, link_rd, link_ts, link_pr, link_qcts, link_raw: Links to specific steps of chapter on Box.
:to_project: Change the project the chapter belongs to.
:to_chapter: Change the chapter number.
:notes: Replaces all the chapters notes with this.