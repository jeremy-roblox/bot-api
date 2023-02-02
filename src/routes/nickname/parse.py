from sanic.response import json
from resources.constants import DEFAULTS
from resources.database import fetch_guild_data
from resources.models import GuildData
import re
import datetime

nickname_template_regex = re.compile(r"\{(.*?)\}")
any_group_nickname = re.compile(r"\{group-rank-(.*?)\}")


class Route:
    PATH = "/nickname/parse/"
    METHODS = ("GET",)

    async def handler(self, request):
        json_body = request.json or {}

        # Requirements
        # ---
        # Code has to have feature parity with the old code, along with ability to handle guilded-related requests
        # It does not need to validate between being for guilded or discord, just proper data needs to be output.
        # ---
        # Templates:
        #   {disable-nicknaming}
        #   {prefix}
        #   {server-name}
        #
        #   {smart-name}
        #   {roblox-name}
        #   {display-name}
        #   {roblox-id}
        #   {roblox-age}
        #   X-{roblox-join-date}
        #
        #   {group-rank-id}
        #   {group-rank}
        #   {group-name}
        #   {group-url}
        #
        #   {discord-name}/{guilded-name}
        #   {discord-nick}/{guilded-nick}
        #   {discord-mention}/{guilded-mention}
        #   {discord-id}/{guilded-id}

        # Discord/Guilded user data
        # Minimum data needed: name, nickname, user id
        #
        # I think expected data should be a dict w/ the vals: "name", "nick", & "id"
        # This should work for both sides, just needs to be set accordingly when sending.
        user_data = json_body.get("user_data")

        # Only need a guild id and a guild name
        guild_id = json_body.get("guild_id")
        guild_name = json_body.get("guild_name")

        # Roblox account data (name, id, displayName, description, groups, groupsv2, etc...)
        roblox_account = json_body.get("roblox_account")

        # The nickname template sent to this api endpoint for processing, defaults to {smart-name}
        template = json_body.get("template") or DEFAULTS.get("nicknameTemplate") or ""

        # Determines if result should be limited to 32 characters or not
        is_nickname = json_body.get("is_nickname") or True

        # Group placholder values
        # group_data should reflect a V2 groups api response for a singular group.
        group = json_body.get("group_data") or None
        group_id = None

        if template == "{disable-nicknaming}":
            return json({"success": True, "nickname": None})

        if roblox_account:
            roblox_username = roblox_account.get("name")
            roblox_display_name = roblox_account.get("displayName")

            if not group:
                guild_data: GuildData = await fetch_guild_data(str(guild_id), "binds")
                group_id = (
                    any(b["bind"]["type"] == "group" for b in guild_data.binds) if guild_data.binds else None
                )

                if group_id:
                    group = roblox_account.get("groupsv2").get(group_id)

            group_role = group.get("role").get("name")

            if "smart-name" in template:
                smart_name = f"{roblox_display_name} (@{roblox_username})"

                if roblox_username == roblox_display_name or len(smart_name) > 32:
                    smart_name = roblox_username

            template = (
                template.replace("roblox-name", roblox_username)
                .replace("display-name", roblox_display_name)
                .replace("smart-name", smart_name)
                .replace("roblox-id", str(roblox_account.get("id")))
                .replace("roblox-age", str(roblox_account.get("age_days")))
                .replace("group-rank", group_role)
            )
        else:
            # Unverified users
            if not template:
                template: str | None = (
                    await fetch_guild_data(str(guild_id), "unverifiedNickname")
                ).unverifiedNickname

            if template == "{disable-nicknaming}":
                return json({"success": True, "nickname": None})

        template = self.parse_capitalization(template)

        return json({"success": True, "nickname": template[:32] if is_nickname else template})

    def parse_capitalization(self, template: str) -> str:
        for outer_nick in nickname_template_regex.findall(template):
            nick_data = outer_nick.split(":")
            nick_fn = None
            nick_value = None

            if len(nick_data) > 1:
                nick_fn = nick_data[0]
                nick_value = nick_data[1]
            else:
                nick_value = nick_data[0]

            # nick_fn = capA
            # nick_value = roblox-name

            if nick_fn:
                if nick_fn in ("allC", "allL"):
                    if nick_fn == "allC":
                        nick_value = nick_value.upper()
                    elif nick_fn == "allL":
                        nick_value = nick_value.lower()

                    template = template.replace("{{{0}}}".format(outer_nick), nick_value)
                else:
                    template = template.replace("{{{0}}}".format(outer_nick), outer_nick)  # remove {} only
            else:
                template = template.replace("{{{0}}}".format(outer_nick), nick_value)
            pass

        return template
