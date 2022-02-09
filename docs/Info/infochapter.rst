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

Arguments
===========

Optional
------------
:project:
    | List of projects the chapters can belong to. [:doc:`/Types/project`]
:tl, rd, ts, pr:
    | List of staff working on respective steps. [:doc:`/Types/staff`]
:chapter_from, chapter_upto:
    | Give a minimum and/or maximum chapter number to look for. [:doc:`/Types/number`]
:chapter:
    | A list of numbers the found chapters can have. [:doc:`/Types/number`]
:id:
    | A list of ids the found chapters can have. [:doc:`/Types/number`]
:release_from, release_upto, release_on:
    | Filter for release Date. [:doc:`/Types/datetime`]
:status:
    | Current status of the chapter. Can be one of "active", "tl", "ts", "rd", "pr", "qcts" or "ready". [:doc:`/Types/literals`]
:fields:
    |  What columns to include in the result table.
     Can be one of "link_tl" ("link_ts", "link_rd", ..),"date", "date_tl", .., "date_rl", "tl", "ts", "rd", "pr", "qcts" or "ready". [:doc:`/Types/literals`]
:links:
    | Either true or false, whether the bot sends the links to each steps of the chapters. [:doc:`/Types/text`]

Related Articles:
^^^^^^^^^^^^^^^^^^^^

You can find a tutorial on how to pass a list of arguments here:
:doc:`/Tutorials/ParamListTut`
