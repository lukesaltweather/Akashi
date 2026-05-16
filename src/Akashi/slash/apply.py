import textwrap

from discord import Client, RadioGroupOption
from discord.ext import commands
import discord

from Akashi.util.context import CstmContext


class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Apply', style=discord.ButtonStyle.blurple, custom_id='persistent_view:apply')
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())


class ApplyModal(discord.ui.Modal, title='Applying to Nekyou'):
    role = discord.ui.Label(
        text='Role',
        component=discord.ui.Select(
            placeholder='Select a role to apply for',
            options=[
                discord.SelectOption(label='JP Translator', value='jptl'),
                discord.SelectOption(label='Typesetter', value='ts'),
                discord.SelectOption(label='Redrawer', value='rd'),
            ],
            max_values=3,
            required=True
        ))
    radio = discord.ui.Label(
        text='Previous Experience',
        description='Do you have any previous experience with scanlating?',
        component=discord.ui.RadioGroup(options=[discord.RadioGroupOption(label='Yes', value='yes'),
                                                 discord.RadioGroupOption(label='No', value='no')], required=True))
    file = discord.ui.Label(
        text='Test Files',
        description='Your completed test files, as jpg or png for RD or TS tests, or the word file for TL tests.',
        component=discord.ui.FileUpload(required=False, max_values=5))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel = await interaction.guild.get_channel(interaction.client.config["server"]["channels"]["applications"]).create_thread(name=interaction.user.display_name, type=discord.ChannelType.private_thread)
        await channel.edit(invitable=False)
        await channel.add_user(interaction.user)
        files = [await file.to_file() for file in self.file.component.values]
        role = await interaction.guild.fetch_role(interaction.client.config["server"]["roles"]["evaluator"])
        await channel.send(files=files,view=ThreadView(roles=self.role.component.values, experience=self.radio.component.value, files=files, avatar_url=interaction.user.display_avatar.url, user_name=interaction.user.display_name))
        await channel.send(role.mention if role else None)
        await interaction.response.send_message(f'Thank you for applying! Please head over to {channel.mention} for anything further related to your application.', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        # await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)



class ThreadView(discord.ui.LayoutView):

    container = discord.ui.Container()

    action_row = discord.ui.ActionRow()

    def __init__(self,  * ,roles: list[str] = None, experience: str = None, files: list[discord.File] = None, avatar_url: str = "", user_name: str = ""):
        super().__init__(timeout=None)
        self.section = discord.ui.Section(accessory=discord.ui.Thumbnail(media=avatar_url))
        self.container.add_item(self.section)
        self.section.add_item(discord.ui.TextDisplay(content=f'# {user_name}'))

        if roles:
            self.section.add_item(
                discord.ui.TextDisplay(content=f'Roles: {", ".join(roles)}')
            )
        if experience:
            self.section.add_item(
                discord.ui.TextDisplay(content=f'Experience: {experience}')
            )
        if files:
            gallery = discord.ui.MediaGallery()
            for file in files:
                if file.filename.endswith('.jpg') or file.filename.endswith('.png') or file.filename.endswith('.jpeg'):
                    gallery.add_item(media=file)
                else:
                    self.add_item(discord.ui.File(media=file))
            if gallery.items:
                self.add_item(gallery)

    @action_row.button(label='Close Application Channel', style=discord.ButtonStyle.red, custom_id='thread_view:close')
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        chn = interaction.channel
        assert isinstance(chn, discord.Thread)
        await chn.edit(archived=True, locked=True, reason='Application channel closed.')
        await interaction.response.defer()

class ApplyC(commands.Cog, name="apply"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
        self.bot.add_view(PersistentView())
        self.bot.add_view(ThreadView())

    @commands.is_owner()
    @commands.command()
    async def apply_message(self, ctx: CstmContext):
        embed = discord.Embed(title="Applying to Nekyou", description=textwrap.dedent(
            """Click the button below to open an application ticket.
                  
            We require you to do a short test, you can find it here:
            https://nekyou.com/join-us/
            If you have previous experience, you may also be able to get accepted without a test, you need to supply us samples of your work however.
                        
            Thanks for your interest!"""),
                              color=discord.Color.blurple())
        await ctx.send(embed=embed, view=PersistentView())


async def setup(bot):
    await bot.add_cog(ApplyC(bot))
