==============================
How to finish a chapter
==============================

To mark a chapter as finished, you use the command [:doc:`/Done/done`].

The command you write must have these three options:

- The chapter
- The *type* of step you have finished, i.e. translation or typeset.
- The link to the finished step on box

A command could look like this:

.. code-block::

    $done chapter: yankee 52 step: ts link: https://box.com/some-link

Let's try to untangle this.

The Dollar Sign ($) is the command prefix. It's at the start of the message, and tells the bot that the following text is a command it must process.
`done` is the command name. Note that there is no space between prefix and command.
Following the command name are the three options the command requires.

.. hint::
    An option consists of three parts. This is based on the style of the Discord search and slash commands.

    +-------------+-------+--------------+
    | Option Name | Colon | Option Value |
    +=============+=======+==============+
    | step        | :     | ts           |
    +-------------+-------+--------------+

    The colon denotes the separation between option name and its corresponding value.

Let's discuss our three options.

chapter
---------------
This is the chapter you were working on.
The value consists of two parts, the project name and the chapter's number.
These are separated by a space. The project name allows for some common short versions, e.g. yankee for Yankee-kun and the white cane girl.
The number may also include a decimal point if necessary.

step
------
This is the step you finished, in it's shortened form.
If you want to tell the bot that you finished typesetting, this is simply "ts".
Other values might be tl, rd, pr or qcts.

link
------
This is the link to the folder on box where you uploaded your finished files.
Simply copy the link from box and paste it here.
