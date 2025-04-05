import asyncio
import logging

from config import DATA_COLLECTION_INTERVAL, STEAM_API_KEY
from db import Database
from discord_bot import DiscordClient
from steam_web_api import Steam


class DataCollector:

    def __init__(self, data, discord_client: DiscordClient, database: Database):
        self.data = data
        self.discord_client = discord_client
        self.db = database
        self.steam = Steam(STEAM_API_KEY)

    async def collect_data(self):
        while True:
            await asyncio.sleep(DATA_COLLECTION_INTERVAL * 60)
            await self.collect_discord_data()
            await self.collect_steam_data()
        pass

    async def collect_discord_data(self):
        if not self.discord_client.is_ready():
            logging.warning("Discord client is not ready.")
            return
        logging.info("Collecting Discord data...")
        for guild in self.discord_client.guilds:
            logging.debug(f"Guild: {guild.name} (ID: {guild.id})")
            if str(guild.id) in self.data["guild_ids"]:
                for channel in guild.voice_channels:
                    user_count = len(channel.members)
                    tracked_users = 0
                    logging.debug(f"Voice channel {channel.name} has {user_count} users.")
                    for member in channel.members:
                        if str(member.id) in self.data["user_discord_ids"]:  # Nur Eingetragene Leute tracken
                            tracked_users += 1
                            self.db.insert_discord_voice_activity(str(member.id), channel.name, str(guild.id))
                            if member.activity:
                                self.db.insert_discord_game_activity(str(member.id), str(member.activity))
                    if user_count > 0:
                        self.db.insert_discord_voice_channel(
                            channel.name,
                            str(guild.id),
                            user_count,
                            tracked_users
                        )
        pass

    async def collect_steam_data(self):
        logging.info("Collecting Steam data...")
        for user in self.data["user_steam_ids"]:
            logging.debug(f"Collecting data for Steam user {user}")
            # Maybe personaname änderungen tracken?
            user = self.steam.users.get_user_details(user)
            if user:
                logging.debug(f"User data: {user}")
                if user["player"].get("gameextrainfo"):
                    logging.debug(f"User is playing: {user["player"]["gameextrainfo"]}")
                    self.db.insert_steam_game_activity(user["player"]["steamid"],user["player"]["gameextrainfo"])
            else:
                logging.debug(f"Failed to collect data for Steam user {user}")
        pass
