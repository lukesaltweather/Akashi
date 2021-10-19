======================================================================
assign
======================================================================
------------------------------------------------------------
Aliases: claim, take
------------------------------------------------------------
Description
==============
Assign a staffmember or yourself for a step on a chapter.

Required Role
=====================
Role `Neko Workers`.

Arguments
===========
Required
---------
:chapter: The chapter to edit, in format: projectName chapterNbr
:step: The step to assign the staffmember to. Can be one of: tl, rd, ts, pr or qc.

Optional
----------
:staff: The person that is assigned. If omitted, the command's author is assigned instead.