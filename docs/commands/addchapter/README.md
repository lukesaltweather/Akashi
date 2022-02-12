---
description: 'Aliases: addc, addch, ac'
---

# $addchapter

## Description

Add a chapter to the database. Should only be done once raws are available. Will return an image showcasing the new chapter.

## Permissions

Requires the `Poweruser` role.

## **P**arameters

#### Required

`-c=` Chapter number. 

`-p=` The project's title or one of its alternative titles.

`-link=` Link to the raws. Alternatively, `-link_raw=` can be used in its place.

#### Optional

`-tl=` Add a translator to the chapter either by id or by username.

`-rd=` Same as `-tl=` but for redrawers.

`-ts=` Same as `-tl=` but for typesetters.

`-pr=` Same as `-tl=` but for proofreaders.

`-link_tl=`Link to translation.

`-link_rd=`Link to redraw.

`-link_ts=`Link to typeset.

`-link_pr=`Link to proofread.

