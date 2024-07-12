#  MIT License
#
#  Copyright (c) 2022 lukesaltweather
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
import typing

import discord

from Akashi.model.chapter import Chapter
from Akashi.util.misc import divide_chunks, format_number


def get_chapter_string(chapter: Chapter):
    chapter_string = (
        f"Ch. {format_number(chapter.number)}: [Raws]({chapter.link_raw}) |"
    )
    if not chapter.translator and not chapter.link_tl:
        chapter_string = chapter_string + " ~~TL~~ |"
    elif chapter.translator and not chapter.link_tl:
        chapter_string = chapter_string + f" **TL** ({chapter.translator.name}) |"
    elif chapter.link_tl:
        chapter_string = "{} [TL ({})]({}) |".format(
            chapter_string,
            chapter.translator.name if chapter.translator else "None",
            chapter.link_tl,
        )

    if not chapter.proofreader and not chapter.link_pr:
        chapter_string = chapter_string + " ~~PR~~ |"
    elif chapter.proofreader and not chapter.link_pr:
        chapter_string = chapter_string + f" **PR** ({chapter.proofreader.name}) |"
    elif chapter.link_pr:
        chapter_string = (
            chapter_string
            + f" [PR ({chapter.proofreader.name if chapter.proofreader else 'None'})]({chapter.link_pr}) |"
        )

    if not chapter.redrawer and not chapter.link_rd:
        chapter_string = chapter_string + " ~~RD~~ |"
    elif chapter.redrawer and not chapter.link_rd:
        chapter_string = chapter_string + f" **RD** ({chapter.redrawer.name}) |"
    elif chapter.link_rd:
        chapter_string = (
            chapter_string
            + f" [RD ({chapter.redrawer.name if chapter.redrawer else 'None'})]({chapter.link_rd}) |"
        )

    if not chapter.typesetter and not chapter.link_ts:
        chapter_string = chapter_string + " ~~TS~~ |"
    elif chapter.typesetter and not chapter.link_ts:
        chapter_string = chapter_string + f" **TS** ({chapter.typesetter.name}) |"
    elif chapter.link_ts:
        chapter_string = (
            chapter_string
            + f" [TS ({chapter.typesetter.name if chapter.typesetter else 'None'})]({chapter.link_ts}) |"
        )

    if not chapter.qualitychecker and not chapter.link_qc:
        chapter_string = chapter_string + " ~~QC~~ |"
    elif chapter.qualitychecker and not chapter.link_qc:
        chapter_string = chapter_string + f" **QC** ({chapter.qualitychecker.name}) |"
    elif chapter.link_qc:
        chapter_string = (
            chapter_string
            + f" [QC ({chapter.qualitychecker.name if chapter.qualitychecker else 'None'})]({chapter.link_qc}) |"
        )

    if chapter.link_rl:
        chapter_string = chapter_string + f" [QCTS]({chapter.link_rl})"
    else:
        chapter_string = chapter_string + f" ~~QCTS~~"
    return chapter_string + "\n"


def join_chapters(chapters: typing.List, project_embed: discord.Embed, heading: str):
    divided_chapters = list(divide_chunks(chapters, 2))
    c = " ".join(b for b in divided_chapters[0])
    project_embed.add_field(name=heading, value=c, inline=False)
    for division in divided_chapters[1:]:
        c = " ".join(b for b in division)
        project_embed.add_field(name="\u200b", value=c, inline=False)
