from lark import Lark, Transformer, visitors
from discord.ext.commands import HybridCommand, Command, MISSING, Context, run_converters, BadArgument

class UnknownFlag(BadArgument):
    def __str__(self) -> str:
        return 'Unknown flag: {}'.format(self.args[0])

class ArgTransformer(Transformer):
    def __init__(self, ctx: Context):
        self.ctx = ctx
    
    def start(self, flags):
        flags = {k:v for k,v in flags}
        return flags

    def flag(self, key, value):
        if key not in self.ctx.command.params:
            raise BadArgument(f"Flag {key} is not a valid flag for this command.")
        return (key, value)

class HybridFlagCommand(HybridCommand):
    def __init__(self, callback, name, **attrs):
        super().__init__(callback, name=name, **attrs)
        self._parser = Lark(f"""
            start: flag+
            flag: STRING ":" WS+ (value | list)
            str: STRING (WS+ STRING)*
            list: value ("," WS+ value)*
            %import common.WS -> WS
            %import common.ESCAPED_STRING -> STRING
        """, start='start') # we can't handle aliases yet

    async def _parse_arguments(self, ctx: Context):
        interaction = ctx.interaction
        if interaction is None:
            return await self.run_parser(ctx)
        else:
            ctx.kwargs = await self.app_command._transform_arguments(interaction, interaction.namespace)

    async def run_parser(self, ctx: Context):
        ctx.args = [ctx] if self.cog is None else [self.cog, ctx]
        content = ctx.view.get()
        transformed = ArgTransformer(ctx).transform(self._parser.parse(content))
        params = self.params
        for k, v in transformed:
            ctx.args[k] = await run_converters(ctx, params[k].converter, v, params[k])

def hybrid_flag_command(func, name=MISSING, **attrs):
    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return HybridFlagCommand(func, name=name, **attrs)

    return decorator


