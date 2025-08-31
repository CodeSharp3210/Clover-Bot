import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

#BOT ABOUT
@bot.event
async def on_ready():
    print(f'Il bot è online come {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Comandi con slash sincronizzati: {len(synced)}')
    except Exception as e:
        print(f'Errore nella sync: {e}')


#CANCELLAZIONE MESSAGGI
ALLOWED_CHANNELS = [1410722461124661440]
@bot.event
async def on_message(message):
    # Ignora i messaggi del bot stesso
    if message.author == bot.user:
        return

    # Verifica che il messaggio sia in un canale specificato
    if message.channel.id in ALLOWED_CHANNELS:
        # Se il messaggio NON è un comando (es. non inizia con il prefisso)
        if not message.content.startswith(bot.command_prefix):
            try:
                await message.delete()
                print("Messaggio eliminato")
            except discord.Forbidden:
                print("Permessi insufficienti per l'eliminazione del messaggio")
            return  # Importante: non processare oltre se il messaggio è stato eliminato

    # Se il messaggio è un comando, gestiscilo normalmente
    await bot.process_commands(message)


#COMANDO /clover
@bot.tree.command(name="clover", description="Il bot risponde con le informazioni riguardo all' APP")
async def cloverinfo(interaction: discord.Interaction):
    await interaction.response.send_message("Clover Client Coded By CodeSharp :)")


#COMANDO /about
@bot.tree.command(name="about", description="Spiega chi è l'autore del server")
async def aboutinfo(interaction: discord.Interaction):
    await interaction.response.send_message("Ciao, io sono Marco e sono anche il creatore di questo Bot dal quale visualizzi questa esperienza. Ho 14 anni e sono uno sviluppatore C# Python e quando mi ci metto so anche il C. Il mio hobby è giocare a Minecraft più precisamente le Bedwars, le Skyblock e i duels su Hypixel; il server multiplayer più grande al mondo. Grazie di aver letto e buona continuazione sul server!")


#COMANDO /tictactoe
# Simboli per i giocatori
PLAYER_SYMBOLS = ["❌", "⭕"]

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y, game):
        super().__init__(label="\u200b", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.game.current_player:
            await interaction.response.send_message("Non è il tuo turno!", ephemeral=True)
            return

        if self.game.board[self.y][self.x] != "":
            await interaction.response.send_message("Questa casella è già occupata!", ephemeral=True)
            return

        symbol = self.game.get_current_symbol()
        self.label = symbol
        self.disabled = True
        self.style = discord.ButtonStyle.success if symbol == "❌" else discord.ButtonStyle.danger
        self.game.board[self.y][self.x] = symbol

        winner = self.game.check_winner()
        if winner:
            for child in self.view.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"{interaction.user.mention} ha vinto!", view=self.view)
        elif self.game.is_draw():
            for child in self.view.children:
                child.disabled = True
            await interaction.response.edit_message(content="È un pareggio!", view=self.view)
        else:
            self.game.switch_turn()
            await interaction.response.edit_message(content=f"Turno di {self.game.current_player.mention}", view=self.view)


class TicTacToeView(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__()
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [["" for _ in range(3)] for _ in range(3)]
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y, self))

    def get_current_symbol(self):
        return PLAYER_SYMBOLS[0] if self.current_player == self.player1 else PLAYER_SYMBOLS[1]

    def switch_turn(self):
        self.current_player = self.player1 if self.current_player == self.player2 else self.player2

    def check_winner(self):
        lines = self.board + list(zip(*self.board))  # righe e colonne
        lines.append([self.board[i][i] for i in range(3)])  # diagonale principale
        lines.append([self.board[i][2 - i] for i in range(3)])  # diagonale secondaria
        for line in lines:
            if line.count(line[0]) == 3 and line[0] != "":
                return line[0]
        return None

    def is_draw(self):
        return all(cell != "" for row in self.board for cell in row)


@bot.tree.command(name="tictactoe", description="Sfida un altro utente a TicTacToe o Tris!")
@app_commands.describe(avversario="L'utente da sfidare")
async def tictactoe(interaction: discord.Interaction, avversario: discord.Member):
    if avversario.bot:
        await interaction.response.send_message("Non puoi sfidare un bot!", ephemeral=True)
        return
    if avversario == interaction.user:
        await interaction.response.send_message("Non puoi sfidare te stesso!", ephemeral=True)
        return

    view = TicTacToeView(interaction.user, avversario)
    await interaction.response.send_message(f"{interaction.user.mention} vs {avversario.mention}\nTurno di {interaction.user.mention}", view=view)


#COMANDO /sassocartaforbici
RPS_OPTIONS = {
    "Sasso": "🪨",
    "Carta": "📄",
    "Forbici": "✂️"
}


class RPSButton(discord.ui.Button):
    def __init__(self, label, user, game):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.choice = label
        self.user = user
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        if interaction.user not in [self.game.player1, self.game.player2]:
            await interaction.response.send_message("Questa partita non è tua!", ephemeral=True)
            return

        if self.game.has_chosen(interaction.user):
            await interaction.response.send_message("Hai già scelto!", ephemeral=True)
            return

        self.game.set_choice(interaction.user, self.choice)
        await interaction.response.send_message(f"Hai scelto {RPS_OPTIONS[self.choice]}", ephemeral=True)

        if self.game.both_chosen():
            result_msg = self.game.get_result_message()
            await self.game.message.edit(content=result_msg, view=None)


class RPSView(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=60)
        self.player1 = player1
        self.player2 = player2
        self.choices = {}
        self.message = None

        for choice in RPS_OPTIONS.keys():
            self.add_item(RPSButton(choice, player1, self))
            self.add_item(RPSButton(choice, player2, self))

    def has_chosen(self, user):
        return user.id in self.choices

    def set_choice(self, user, choice):
        self.choices[user.id] = choice

    def both_chosen(self):
        return len(self.choices) == 2

    def get_result_message(self):
        c1 = self.choices[self.player1.id]
        c2 = self.choices[self.player2.id]

        emoji1 = RPS_OPTIONS[c1]
        emoji2 = RPS_OPTIONS[c2]

        result = self.determine_winner(c1, c2)

        if result == 0:
            outcome = "Pareggio!"
        elif result == 1:
            outcome = f"{self.player1.mention} ha vinto!"
        else:
            outcome = f"{self.player2.mention} ha vinto!"

        return f"{self.player1.mention} ha scelto {emoji1}\n{self.player2.mention} ha scelto {emoji2}\n\n**{outcome}**"

    @staticmethod
    def determine_winner(c1, c2):
        if c1 == c2:
            return 0
        wins = {"Sasso": "Sasso", "Forbici": "Carta", "Carta": "Sasso"}
        return 1 if wins[c1] == c2 else 2


@bot.tree.command(name="sassocartaforbici", description="Sfida un altro utente a Sasso Carta Forbici")
@app_commands.describe(avversario="L'utente da sfidare")
async def rps(interaction: discord.Interaction, avversario: discord.Member):
    if avversario.bot:
        await interaction.response.send_message("Non puoi sfidare un bot!", ephemeral=True)
        return
    if avversario == interaction.user:
        await interaction.response.send_message("Non puoi sfidare te stesso!", ephemeral=True)
        return

    view = RPSView(interaction.user, avversario)
    msg = await interaction.response.send_message(
        f"{interaction.user.mention} vs {avversario.mention}\nScegli sasso, carta o forbici!", view=view
    )
    view.message = await interaction.original_response()


#COMANDO /shadowoptimizer
@bot.tree.command(name="shadowoptimizer", description="ShadowOptimizer è ora gratuito")
async def shadowinfo(interaction: discord.Interaction):
    await interaction.response.send_message("Shadow Optimizer è ora gratuito in tutte le sue versioni + il codice su github.com/CodeSharp3210")


#COMANDO /register
@bot.tree.command(name="register", description="Consente di registrarsi al Server in modo da avere un esperienza completa")
async def registerinfo(interaction: discord.Interaction, username: discord.Member):
    if username == interaction.user:
        await interaction.response.send_message("Registrazione completata con successo!")
    else:
        await interaction.response.send_message("Non devi eseguire la registrazione con un altro profilo o se valido riprovare!")


#COMANDO /bundle
@bot.tree.command(name="bundle", description="Consente di vedere il Bundle attuale del server")
async def bundle(interaction: discord.Interaction):
    await interaction.response.send_message("Il Bundle attuale del Server è: Summer Bundle. Puoi acquistarlo creando un ticket in <#1405217609573470270>")
   

#COMANDO /vip
@bot.tree.command(name="vip", description="Consente di visionare il VIP del server")
async def vip(interaction: discord.Interaction):
    await interaction.response.send_message("Il VIP ti consente di boostarmi e di supportarmi. Il costo è di 10 EUR e se vuoi aquistarlo assicurati di fare un ticket in <#1405217609573470270>")


# TOKEN BOT

bot.run("BOT_ID")
