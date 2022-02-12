from src.util.flags.flagutils import ChapterFlags


class AddNoteFlags(ChapterFlags):
    text: str


class RemoveNoteFlags(ChapterFlags):
    pass


class PurgeNotesFlags(ChapterFlags):
    pass
