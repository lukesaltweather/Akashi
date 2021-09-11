======================================================================
infochapter
======================================================================
------------------------------------------------------------
Aliases: infochapters, ic, infoc
------------------------------------------------------------
Description
==============
Get info on chapters.

Required Role
=====================
Role `Neko Workers`.

Parameters
===========

Optional
------------
:project: List of projects the chapters can belong to.
:tl, rd, ts, pr: List of staff working on respective steps.
:chapter_from, chapter_upto: Give a minimum and/or maximum chapter number to look for.
:chapter: A list of numbers the found chapters can have.
:id: A list of ids the found chapters can have.
:release_from, release_upto, release_on: Filter for release Date.
:status: Current status of the chapter. Can be one of "active", "tl", "ts", "rd", "pr", "qcts" or "ready".
:fields: What columns to include in the result table.
:links: Either true or false, whether the bot sends the links to each steps of the chapters.

Related Articles:
^^^^^^^^^^^^^^^^^^^^

You can find a tutorial on how to pass a list of arguments here:
:doc:`/Tutorials/ParamListTut`

Dates have to be in following format:
:doc:`/Tutorials/DateTutorial`