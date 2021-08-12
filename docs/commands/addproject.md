---
description: 'Aliases: ap, addp, addproj'
---

# $addproject

## Description

Add a project to the database.

## Permissions

Requires the `Poweruser` role.

## Parameters

### Required

`-title=` The project's title.

`-status=` The project's current status. \(Mostly either _active_ or _inactive_\)

`-altNames=` Alternative titles that are often used within the group, e.g. _YanGaru_ for _Yankee-kun to Hakujou Gaaru._ Separated by comma.

`-link=` The link to the box project folder.

### Optional

`-icon=` Directlink to an image that is going to be used as the little icon next to the project's title in the infoboard.

`-thumbnail=` Directlink to an image  that is going to be used in the infoboard as the thumbnail of the project.

`-tl= -rd= -ts= -pr=` Any \(or none\) of these parameters can be used to assign a default staffmember to a project.

