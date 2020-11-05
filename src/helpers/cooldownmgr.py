import asyncio
import typing

class CooldownManager:
    """Track XP cooldowns of members
    """

    __slots__ = ("__dict__", "_cooldown", "_messages", "_tasks")

    def __init__(self, cooldown: float):
        self._loop = asyncio.get_running_loop()
        self._cooldown = cooldown
        self._messages = []
        self._tasks = {}

    def add(self, author: int):
        self._messages.append(author)
        self._tasks[author] = self._loop.create_task(self._remove(author))

    async def _remove(self, author: int):
        await asyncio.sleep(self._cooldown)
        self._messages.remove(author)
        self._tasks.pop(author)

    def on_cooldown(self, author: int) -> bool:
        return author in self._messages

    def cancel_cooldown(self, author: typing.Optional[int] = None):
        if author:
            if task := self._tasks.pop(author, None):
                task.cancel()
                return
            raise LookupError("Couldn't find a Cooldown for this author.")
        for task in self._tasks:
            task.cancel()