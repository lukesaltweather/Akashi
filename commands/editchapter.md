---
description: 'Aliases: ec, editc, editch'
---

# $editchapter

## Description

Edit a chapter in the database. Select chapter by project and chapter number, or by internal chapter id. React with the Emoji's to either confirm or dump the changes.

## Permissions

Requires the `Poweruser` role.

## **P**arameters

### Required

`-c=` Chapter number. 

`-p=` The project's title or one of its alternative titles.

Alternatively:

`-id=` Select chapter by id.



### Optional

<table>
  <thead>
    <tr>
      <th style="text-align:left">Parameter</th>
      <th style="text-align:left">Explanation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:left">-title=</td>
      <td style="text-align:left">Change title.</td>
    </tr>
    <tr>
      <td style="text-align:left">-tl= -rd= -ts= -pr=</td>
      <td style="text-align:left">Set staffmember either by
        <br />discord ID or username.</td>
    </tr>
    <tr>
      <td style="text-align:left">-link_raw= -link_tl= -link_rd=
        <br />-link_ts= -link_pr= -link_qcts=</td>
      <td style="text-align:left">Change link of specific step.</td>
    </tr>
    <tr>
      <td style="text-align:left">-date_rl= -date_tl= -date_rd=
        <br />-date_ts= -date_pr= -date_qcts=</td>
      <td style="text-align:left">
        <p>Set date of a specific task finishing. Format below.</p>
        <p><em><b>(rl = Release in this case.)</b></em>
        </p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left">-to_project=</td>
      <td style="text-align:left">Assign a different project to the chapter.</td>
    </tr>
    <tr>
      <td style="text-align:left">-to_chapter=</td>
      <td style="text-align:left">Assign the chapter a new chapter number.</td>
    </tr>
    <tr>
      <td style="text-align:left">-notes=</td>
      <td style="text-align:left">Directly alter the chapter&apos;s notes. Not recommended.</td>
    </tr>
  </tbody>
</table>

{% hint style="info" %}
The bot always uses YYYY MM DD as its date format. Exactly this way, with the spaces included. It won't accept any other formats.
{% endhint %}

{% hint style="info" %}
To set a value to NULL, simply don't write anything after the `=`.
{% endhint %}



