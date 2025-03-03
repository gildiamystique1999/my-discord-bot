import discord
from discord.ext import commands
import asyncio
import logging
from keep_alive import keep_alive  # Importujemy serwer Flask

keep_alive()  # Utrzymuje bota online

# Konfiguracja logowania do konsoli
logging.basicConfig(level=logging.INFO)

# Stałe ID (do uzupełnienia rzeczywistymi wartościami)
GUILD_ID = 1240979152698609714  # ID serwera Discord
PANEL_CHANNEL_ID = 1344637087814783087  # ID kanału #panel-rekrutacyjny
LOG_CHANNEL_ID = 1344255735080419379  # ID kanału logów rekrutacji
REKRUT_ROLE_ID = 1264205670656245791  # ID roli "Rekrut"
RECRUITER_ROLE_ID = 1344637771620548669  # ID roli uprawnionej do rekrutacji (np. "Rekruter" lub admin)
VOICE_CATEGORY_ID = 1263582509136875641  # Opcjonalnie: ID kategorii dla kanałów rozmów (None, jeśli nie dotyczy)

# Ustawienia intencji (wymagane dla member join i voice state)
intents = discord.Intents.default()
intents.members = True  # obsługa zdarzeń dołączania użytkowników
intents.voice_states = True  # obsługa zdarzeń głosowych (do śledzenia rozmów)
# Nie potrzebujemy intents.message_content (używamy przycisków/modalu zamiast komend tekstowych)

bot = commands.Bot(command_prefix="!", intents=intents)

# Słownik globalny do śledzenia aktywnych kanałów rozmów (voice_channel_id -> view procesu rekrutacji)
active_interviews = {}


@bot.event
async def on_ready():
    logging.info(f"Zalogowano jako {bot.user} (ID: {bot.user.id})")
    logging.info("Bot jest gotowy do pracy.")


@bot.event
async def on_member_join(member: discord.Member):
    """Wysyła powitalne DM z przyciskiem do formularza po dołączeniu nowego użytkownika."""
    welcome_message = (
        f"Witaj na serwerze **{member.guild.name}**!\n"
        "Aby rozpocząć rekrutację, kliknij przycisk poniżej i wypełnij formularz rekrutacyjny.\n"
        "Powodzenia!")
    try:
        view = WelcomeView()
        await member.send(welcome_message, view=view)
    except discord.Forbidden:
        logging.warning(
            f"Nie udało się wysłać powitania do {member} (możliwe wyłączone DM)."
        )


class ApplicationModal(discord.ui.Modal, title="Formularz Rekrutacyjny"):
    """Modal z pytaniami rekrutacyjnymi."""
    pyt1 = discord.ui.TextInput(label="Twój nick i lvl z gry?",
                                placeholder="Podaj swój nick i lvl",
                                required=True,
                                max_length=500)
    pyt2 = discord.ui.TextInput(label="Czego oczekujesz od gildii?",
                                style=discord.TextStyle.long,
                                placeholder="Czego od nas oczekujesz...",
                                required=True,
                                max_length=500)
    pyt3 = discord.ui.TextInput(label="Co możesz zaoferować swojej gildii?",
                                style=discord.TextStyle.long,
                                placeholder="Odpowiedz na pytanie...",
                                required=True,
                                max_length=500)
    pyt4 = discord.ui.TextInput(label="Klasa i profesja?",
                                placeholder="Wojownik body itd",
                                required=True,
                                max_length=100)
    pyt5 = discord.ui.TextInput(
        label="Na jakim etapie gry jesteś?",
        style=discord.TextStyle.long,
        placeholder=
        "Napisz nam jak wygląda twoje eq i na jakim etapie jesteś...",
        required=False,
        max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        """Obsługa przesłania formularza rekrutacyjnego przez kandydata."""
        user = interaction.user  # discord.User (DM context)
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            await interaction.response.send_message(
                "Błąd: Nie znaleziono serwera.", ephemeral=True)
            return
        member = guild.get_member(user.id)
        if member is None:
            await interaction.response.send_message(
                "Błąd: Nie znaleziono użytkownika na serwerze.",
                ephemeral=True)
            return

        # Przygotuj embed z pytaniami i odpowiedziami
        embed = discord.Embed(title="Nowe podanie rekrutacyjne",
                              color=discord.Color.blue())
        embed.set_author(name=f"{member.name}#{member.discriminator}",
                         icon_url=member.display_avatar.url)
        embed.add_field(name="**Pytanie 1: Twój nick i wiek**",
                        value=self.pyt1.value or "*(brak odpowiedzi)*",
                        inline=False)
        embed.add_field(name="**Pytanie 2: Czego od nas oczekujesz?**",
                        value=self.pyt2.value or "*(brak odpowiedzi)*",
                        inline=False)
        embed.add_field(name="**Pytanie 3: Co możesz zaoferować gildii??**",
                        value=self.pyt3.value or "*(brak odpowiedzi)*",
                        inline=False)
        embed.add_field(name="**Pytanie 4: Twoja klasa i profesja?**",
                        value=self.pyt4.value or "*(brak odpowiedzi)*",
                        inline=False)
        embed.add_field(name="**Pytanie 5: Na jakim etapie gry jesteś?**",
                        value=self.pyt5.value
                        or "*(brak dodatkowych informacji)*",
                        inline=False)
        embed.set_footer(text=f"ID kandydata: {member.id}")

        panel_channel = bot.get_channel(PANEL_CHANNEL_ID)
        if not panel_channel:
            await interaction.response.send_message(
                "Błąd: Nie znaleziono kanału rekrutacyjnego.", ephemeral=True)
            return

        # Wyślij podanie na kanał rekrutacyjny z przyciskami dla rekruterów
        view = RecruitmentPanelView(candidate=member)
        await panel_channel.send(
            content=f"**Nowe podanie od użytkownika {member.mention}**",
            embed=embed,
            view=view)
        # Potwierdź kandydatowi w DM wysłanie podania
        await interaction.response.send_message(
            "Dziękujemy za wypełnienie formularza! Twoje podanie zostało przesłane do rekruterow. Poczekaj aż rekruter rozpocznie rozmowę głosową jeśli jest obecny z całą pewnościa to długo nie potrwa. Dostaniesz wiadomość o obecności rekrutera.",
            ephemeral=True)


class WelcomeView(discord.ui.View):
    """Widok DM powitalnego z przyciskiem do otwarcia formularza."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 Wypełnij formularz",
                       style=discord.ButtonStyle.primary)
    async def open_form(self, interaction: discord.Interaction,
                        button: discord.ui.Button):
        """Po kliknięciu 'Wypełnij formularz' otwiera modal z podaniem."""
        await interaction.response.send_modal(ApplicationModal())


class RecruitmentPanelView(discord.ui.View):
    """Widok na kanale panelu rekrutacyjnego z przyciskami rozmowy i decyzji."""

    def __init__(self, candidate: discord.Member):
        super().__init__(timeout=None)
        self.candidate = candidate  # Obiekt kandydata (Member)
        self.voice_channel: discord.VoiceChannel = None
        self.recruiter: discord.Member = None  # Rekruter prowadzący rozmowę
        self.conversation_started = False  # Czy rozmowa się rozpoczęła (obie strony weszły)
        self.reminder_task: asyncio.Task = None
        self.timeout_task: asyncio.Task = None

    @discord.ui.button(label="🎤 Rozpocznij rozmowę",
                       style=discord.ButtonStyle.secondary)
    async def start_interview(self, interaction: discord.Interaction,
                              button: discord.ui.Button):
        """Rekruter kliknął przycisk rozpoczęcia rozmowy rekrutacyjnej."""
        guild = interaction.guild
        if guild is None:
            return
        user = interaction.user  # rekruter (Member) który kliknął
        recruiter_role = guild.get_role(RECRUITER_ROLE_ID)
        # Sprawdź uprawnienia rekrutera
        if recruiter_role not in user.roles and not user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Nie masz uprawnień do rozpoczęcia rozmowy.", ephemeral=True)
            return
        if self.voice_channel is not None:
            await interaction.response.send_message(
                "Kanał do rozmowy już został utworzony.", ephemeral=True)
            return

        self.recruiter = user
        # Ustaw permisje dla kanału głosowego: tylko rekruter i kandydat
        overwrites = {
            guild.default_role:
            discord.PermissionOverwrite(view_channel=False, connect=False),
            self.candidate:
            discord.PermissionOverwrite(view_channel=True,
                                        connect=True,
                                        speak=True),
            self.recruiter:
            discord.PermissionOverwrite(view_channel=True,
                                        connect=True,
                                        speak=True)
        }
        # Jeśli chcesz wpuścić wszystkich z roli rekruter, usuń ograniczenie powyżej i użyj:
        # if recruiter_role:
        #     overwrites[recruiter_role] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)

        channel_name = f"Rozmowa rekrutacyjna - {self.candidate.name}"
        category = guild.get_channel(
            VOICE_CATEGORY_ID) if VOICE_CATEGORY_ID else None
        try:
            self.voice_channel = await guild.create_voice_channel(
                channel_name,
                overwrites=overwrites,
                category=category,
                reason="Rozpoczęcie rozmowy rekrutacyjnej")
        except Exception as e:
            await interaction.response.send_message(
                f"Błąd przy tworzeniu kanału głosowego: {e}", ephemeral=True)
            return

        # Zapisz kanał do słownika aktywnych rozmów
        active_interviews[self.voice_channel.id] = self

        # Potwierdź utworzenie kanału (wiadomość w panelu rekrutacyjnym)
        await interaction.response.send_message(
            f"✅ Utworzono kanał głosowy {self.voice_channel.mention} dla rozmowy rekrutacyjnej.",
            ephemeral=False)
        # Wyślij DM do kandydata z informacją o rozpoczęciu rozmowy
        try:
            await self.candidate.send(
                f"🎤 Rozmowa rekrutacyjna została rozpoczęta. Dołącz do kanału głosowego **{self.voice_channel.name}** "
                "na serwerze, aby wziąć udział w rozmowie. Masz 30 minut na dołączenie, inaczej podanie zostanie anulowane."
            )
        except Exception as e:
            logging.warning(
                f"Nie udało się wysłać DM do kandydata o rozpoczęciu rozmowy: {e}"
            )

        # Zaloguj start rozmowy na kanale logów
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"🎤 Rozpoczęto rozmowę rekrutacyjną dla kandydata {self.candidate.mention} "
                f"(Kanał: **{self.voice_channel.name}**). Rekruter: {user.mention}"
            )

        # Uruchom zadania: przypomnienie (10 min) i automatyczny timeout (30 min)
        self.reminder_task = asyncio.create_task(
            self._reminder_after_delay(600))
        self.timeout_task = asyncio.create_task(
            self._timeout_after_delay(1800))

        # Wyłącz przycisk rozpoczęcia rozmowy (by nie tworzyć kolejnych)
        button.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="✅ Akceptuj", style=discord.ButtonStyle.success)
    async def accept_application(self, interaction: discord.Interaction,
                                 button: discord.ui.Button):
        """Rekruter kliknął akceptację podania."""
        guild = interaction.guild
        if guild is None:
            return
        user = interaction.user  # rekruter (Member)
        recruiter_role = guild.get_role(RECRUITER_ROLE_ID)
        if recruiter_role not in user.roles and not user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "Nie masz uprawnień do akceptowania podania.", ephemeral=True)
            return

        # Anuluj ewentualne zaplanowane zadania (przypomnienie/timeout)
        if self.reminder_task:
            self.reminder_task.cancel()
        if self.timeout_task:
            self.timeout_task.cancel()

        # Usuń kanał głosowy (jeśli istnieje)
        if self.voice_channel:
            channel_id = self.voice_channel.id
            try:
                await self.voice_channel.delete(
                    reason="Zakończenie rekrutacji - kandydat zaakceptowany")
            except Exception as e:
                logging.error(f"Błąd przy usuwaniu kanału głosowego: {e}")
            active_interviews.pop(channel_id, None)
            self.voice_channel = None

        # Nadaj rolę "Rekrut" kandydatowi
        rekrut_role = guild.get_role(REKRUT_ROLE_ID)
        if rekrut_role:
            try:
                await self.candidate.add_roles(
                    rekrut_role, reason="Rekrutacja zaakceptowana")
            except Exception as e:
                logging.error(f"Nie udało się nadać roli Rekrut: {e}")

        # Wyślij DM do kandydata o akceptacji
        try:
            await self.candidate.send(
                "Gratulacje! Twoje podanie zostało **zaakceptowane**. Otrzymujesz rolę **Rekrut** na serwerze. Witamy w zespole!"
            )
        except Exception as e:
            logging.warning(f"Nie udało się wysłać DM o akceptacji: {e}")

        # Zaloguj akceptację na kanale logów
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"✅ Podanie kandydata **{self.candidate}** (ID: {self.candidate.id}) "
                f"zostało zaakceptowane przez {user.mention}. Nadano rolę Rekrut."
            )
        # Powiadom na kanale panelu rekrutacyjnego
        await interaction.response.send_message(
            f"✅ Podanie kandydata {self.candidate.mention} zostało **zaakceptowane**.",
            ephemeral=False)

        # Wyłącz wszystkie przyciski po decyzji
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        self.stop()

    @discord.ui.button(label="❌ Odrzuć", style=discord.ButtonStyle.danger)
    async def reject_application(self, interaction: discord.Interaction,
                                 button: discord.ui.Button):
        """Rekruter kliknął odrzucenie podania."""
        guild = interaction.guild
        if guild is None:
            return
        user = interaction.user  # rekruter (Member)
        recruiter_role = guild.get_role(RECRUITER_ROLE_ID)
        if recruiter_role not in user.roles and not user.guild_permissions.kick_members:
            await interaction.response.send_message(
                "Nie masz uprawnień do odrzucenia podania.", ephemeral=True)
            return

        # Anuluj zaplanowane zadania (przypomnienie/timeout)
        if self.reminder_task:
            self.reminder_task.cancel()
        if self.timeout_task:
            self.timeout_task.cancel()

        # Usuń kanał głosowy (jeśli istnieje)
        if self.voice_channel:
            channel_id = self.voice_channel.id
            try:
                await self.voice_channel.delete(
                    reason="Zakończenie rekrutacji - kandydat odrzucony")
            except Exception as e:
                logging.error(f"Błąd przy usuwaniu kanału: {e}")
            active_interviews.pop(channel_id, None)
            self.voice_channel = None

        # Wyślij DM do kandydata o odrzuceniu
        try:
            await self.candidate.send(
                "Dziękujemy za zainteresowanie, jednak Twoje podanie zostało **odrzucone**. "
                "Zostaniesz usunięty z serwera. Powodzenia następnym razem!")
        except Exception as e:
            logging.warning(f"Nie udało się wysłać DM o odrzuceniu: {e}")

        # Wyrzuć kandydata z serwera
        try:
            await self.candidate.kick(reason="Podanie odrzucone")
        except Exception as e:
            logging.error(f"Nie udało się wyrzucić kandydata: {e}")

        # Zaloguj odrzucenie na kanale logów
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"❌ Podanie kandydata **{self.candidate}** (ID: {self.candidate.id}) "
                f"zostało odrzucone przez {user.mention}. Użytkownik został wyrzucony z serwera."
            )
        # Powiadom na kanale panelu rekrutacyjnego
        await interaction.response.send_message(
            f"❌ Podanie kandydata {self.candidate.mention} zostało **odrzucone**.",
            ephemeral=False)

        # Wyłącz wszystkie przyciski
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        self.stop()

    async def _reminder_after_delay(self, delay: float):
        """Wysyła przypomnienie po 10 minutach, jeśli rozmowa się nie rozpoczęła."""
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return  # przerwane (rozmowa już się rozpoczęła lub zakończyła)
        if self.conversation_started or self.voice_channel is None:
            return
        # Sprawdź, kto jest (lub nie) na kanale głosowym
        if self.voice_channel:
            members_in_channel = self.voice_channel.members
            candidate_in_voice = any(m.id == self.candidate.id
                                     for m in members_in_channel)
            recruiter_in_voice = any(
                m.id == self.recruiter.id
                for m in members_in_channel) if self.recruiter else False

            # Wyślij przypomnienia do brakujących osób
            if not candidate_in_voice:
                try:
                    await self.candidate.send(
                        "Przypomnienie: rozmowa rekrutacyjna jeszcze się nie rozpoczęła. "
                        "Dołącz do kanału głosowego w ciągu 20 minut, w przeciwnym razie podanie zostanie anulowane."
                    )
                except Exception as e:
                    logging.warning(
                        f"Nie udało się wysłać przypomnienia do kandydata: {e}"
                    )
            if self.recruiter and not recruiter_in_voice:
                try:
                    await self.recruiter.send(
                        f"Przypomnienie: rozmowa z kandydatem {self.candidate.display_name} jeszcze się nie rozpoczęła. "
                        "Masz 20 minut na przeprowadzenie rozmowy, inaczej podanie zostanie anulowane."
                    )
                except Exception as e:
                    logging.warning(
                        f"Nie udało się wysłać przypomnienia do rekrutera: {e}"
                    )

            # Zaloguj przypomnienie w kanału logów
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(
                    f"⏰ Minęło 10 minut, a rozmowa rekrutacyjna z kandydatem **{self.candidate.display_name}** jeszcze się nie rozpoczęła."
                )

    async def _timeout_after_delay(self, delay: float):
        """Anuluje podanie po 30 minutach, jeśli rozmowa się nie odbyła."""
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        if self.conversation_started or self.voice_channel is None:
            return
        # Usuń kanał głosowy (jeśli jeszcze istnieje)
        if self.voice_channel:
            channel_id = self.voice_channel.id
            try:
                await self.voice_channel.delete(
                    reason="Podanie anulowane - nie odbyto rozmowy w czasie")
            except Exception as e:
                logging.error(f"Błąd przy usuwaniu kanału (timeout): {e}")
            active_interviews.pop(channel_id, None)
            self.voice_channel = None

        # Poinformuj kandydata (DM) i usuń z serwera
        try:
            await self.candidate.send(
                "Niestety rozmowa rekrutacyjna nie doszła do skutku na czas. Twoje podanie zostało anulowane."
            )
        except Exception as e:
            logging.warning(
                f"Nie udało się wysłać DM o anulowaniu podania: {e}")
        try:
            await self.candidate.kick(
                reason=
                "Nie stawił się na rozmowę rekrutacyjną w wyznaczonym czasie")
        except Exception as e:
            logging.error(
                f"Nie udało się wyrzucić kandydata po upływie czasu: {e}")

        # Zaloguj anulowanie na kanale logów
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"❌ Podanie kandydata **{self.candidate}** (ID: {self.candidate.id}) zostało anulowane "
                "(rozmowa nie odbyła się w ciągu 30 minut).")
        # Powiadom na kanale rekrutacyjnym
        panel_channel = bot.get_channel(PANEL_CHANNEL_ID)
        if panel_channel:
            await panel_channel.send(
                f"❌ Podanie kandydata {self.candidate.mention} zostało anulowane z powodu braku rozmowy w wyznaczonym czasie."
            )

        # Wyłącz interakcje i zakończ view
        for child in self.children:
            child.disabled = True
        self.stop()


@bot.event
async def on_voice_state_update(member: discord.Member,
                                before: discord.VoiceState,
                                after: discord.VoiceState):
    """Śledzi wejścia na kanały głosowe, by wykryć rozpoczęcie rozmowy (kandydat + rekruter)."""
    # Jeśli użytkownik dołączył do jakiegoś kanału głosowego
    if after.channel and after.channel.id in active_interviews:
        view = active_interviews[after.channel.id]
        if not view.conversation_started:
            # Sprawdź, czy na kanale są już i kandydat, i rekruter
            channel_members = after.channel.members
            candidate_in = any(m.id == view.candidate.id
                               for m in channel_members)
            recruiter_in = view.recruiter is not None and any(
                m.id == view.recruiter.id for m in channel_members)
            if candidate_in and recruiter_in:
                view.conversation_started = True
                # Anuluj timeout no-show, skoro rozmowa doszła do skutku
                if view.timeout_task:
                    view.timeout_task.cancel()
                # Zaloguj fakt rozpoczęcia rozmowy
                log_channel = bot.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"ℹ️ Rozmowa rekrutacyjna z kandydatem **{view.candidate.display_name}** właśnie się rozpoczęła "
                        "(obie strony dołączyły do kanału).")
    # (Nie musimy obsługiwać opuszczenia kanału, decyzje są podejmowane manualnie.)


keep_alive()  # Utrzymuje bota online
bot.run(
    "MTM0NDYyOTUxMjQ5NDY0NTI3OQ.GxTXDv.sZxIB7SIHIBWNOM1Avl_B_fKb3VM4dEjBScgBg")
