======================================================================
done
======================================================================
------------------------------------------------------------
Aliases: 
------------------------------------------------------------
Description
==============
Mark a specific step of a chapter as finished.
Will prompt for an answer, click on the corresponding emoji reaction.
The options are: Ping the next member with a proper notification appearing for them,
or instead ping, but don't send out a (for some people annoying) notification.

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
    | The step you have finished. Can be one of: tl, rd, ts, pr or qc. [:doc:`/Types/literals`]
:link:
    | The link to the folder on box. [:doc:`/Types/Text`]

Optional
----------
:note:
    | Add a note to the chapters notes. [:doc:`/Types/Text`]