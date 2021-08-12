# Using the bot in practice

## A title.

Hello again! This article will go a little more into detail on how to actually use the bot in practice.

## I want to know things!

A very common usecase you'll encounter with the bot. I will go over two examples here, for a list of all possibilities head over to [infochapter](../commands/infochapter.md) or [infoproject](../commands/infoproject.md).

#### Example 1

Imagine this: wordref thinks Eggy is overworking herself. _How could wordref proof this is the case?_

```text
$infochapter -rd=abluey -rd_from=2020 03 20
```

Let's go over this quickly. `-rd=` filters out all chapters eggy didn't / doesn't redraw. The `-rd_from=` filters by the date the redraw was completed, meaning current redraws and older redraws won't show up.

{% hint style="info" %}
Note that at the moment these parameters are all connected by AND, not by OR. This means that the more parameters you give, the more the results are narrowed down. This is subject to change soon-ish.
{% endhint %}

#### Example 2

In this scenario you want to know the default staff of a project.

```text
$infoproject -title=Yankee-kun -fields=ts,tl,rd,pr
```

The title argument gives us only the specific project we want. The fields argument tells the bot what information to return. 

## Other commands

Other commands you might end up using more often are the "done" commands. These are used to tell the bot that you finished the step of a chapter. They come in different flavours: [donetl](../commands/donetl.md), [donerd](../commands/donerd.md), [donets](../commands/donets.md), [donepr](../commands/donepr.md), [doneqcts](../commands/doneqcts.md).

They automatically fill in the correct date and time, update the step with the link you gave it, and will notify the next member in line. You can also tell it not to ping the next staffmember, like when you're doing the next step yourself.

[note](../commands/note.md) and [addnote](../commands/addnote.md) can be used to view and add notes to a chapter.

$help can be used to send yourself all available commands, as well as to get help for a specific command, via $help &lt;your command&gt;.

[mycurrent](../commands/mycurrent.md) can be used to view all of your currently unfinished chapters.

[release](../commands/release.md) can be used to quickly mark a chapter as released/finished.

