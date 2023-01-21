from sanic.response import json



class Route:
    PATH = "/nickname/parse/"
    METHODS = ("GET", )

    async def handler(self, request):
        json_body = request.json or {}

        template = json_body.get("template")
        roblox_account = json_body.get("roblox_account")
        user_id = json_body.get("user_id")

        if template == "{disable-nicknaming}":
            return json({
                "success": True,
                "nickname": None
            })


