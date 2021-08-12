---
description: 'Aliases: r'
---

# $remind

## Description

Will remind a staffmember through a PM.

## Permissions

Requires the `Neko Worker` role.

## Parameters

### Required

`-msg=` Reminder Message.

`-date=` Date and time when the bot reminds staffmember. Can be in any non-ambiguous format.

#### Optional

`-u=` The member you want to remind of something. If not given, will remind command author.

`-tz=` IANA style timezone you used for the remind datetime. If not given, UTC is assumed.

