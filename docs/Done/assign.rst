======================================================================
assign
======================================================================
------------------------------------------------------------
Aliases: claim, take
------------------------------------------------------------
Description
==============
Assign a staffmember (or yourself) for a step on a chapter.

Required Role
=====================
Role `Neko Workers`.

Arguments
===========
Required
---------
:chapter: 
    | The chapter to edit, in format: projectName chapterNbr [:doc:`/Types/chapter`]
:step: 
    | The step to assign the staffmember to. Can be one of: tl, rd, ts, pr or qc. [:doc:`/Types/literals`]
:link:
    | The link to the folder on box. [:doc:`/Types/Text`]
Optional
----------
:staff: 
    | The staffmember to assign. If omitted, the command's author is assigned instead. [:doc:`/Types/literals`]