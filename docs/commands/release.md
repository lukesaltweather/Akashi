# $release

## Description

This marks a chapter as released. It will not actually release the chapter. Sets the datetime of the release to the current time. \(in UTC\)

## Permissions

Requires role `Poweruser`.

## Parameters

### Required

`-p=` The project's title.

`-c=` The chapter's number.

#### Alternatively:

`-id=` Select chapter by ID instead of using `-p=` and `-c=`.

### Optional

`-date=` Set the date of the release manually.

{% hint style="info" %}
The bot always uses YYYY MM DD as its date format. Exactly this way, with the spaces included. It won't accept any other formats.
{% endhint %}



