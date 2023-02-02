from sanic.response import json
import re

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

        # The nickname template sent to this api endpoint for processing
        template = json_body.get("template")

        if template == "{disable-nicknaming}":
            return json({"success": True, "nickname": None})
