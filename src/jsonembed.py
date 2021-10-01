from __future__ import annotations

import json

import discord


def json_to_embed(string : str) -> discord.Embed:
    """Convert a json string to a discord embed

    Args:
        string (str): JSON string

    Returns:
        discord.Embed: Resulting embed
    """
    data = json.loads(string)

    embed = discord.Embed()
    empty = discord.Embed.Empty

    for field in ("title", "description", "color", "url"):
        if field in data and data[field] != "" and data[field] is not None:
            setattr(embed, field, data[field])
        else:
            setattr(embed, field, empty)

    if "author" in data:
        if "name" in data["author"] and data["author"]["name"] != "" and data["author"]["name"] is not None:
            name = data["author"]["name"]
        else:
            name = empty

        if "url" in data["author"] and data["author"]["url"] != "" and data["author"]["url"] is not None:
            url = data["author"]["url"]
        else:
            url = empty

        if "icon" in data["author"] and data["author"]["icon"] != "" and data["author"]["icon"] is not None:
            icon = data["author"]["icon"]
        else:
            icon = empty

        if name != empty or url != empty or icon != empty:
            embed.set_author(name=name, url=url, icon_url=icon)

    if "thumbnail" in data and data["thumbnail"] != "" and data["thumbnail"] is not None:
        embed.set_thumbnail(url=data["thumbnail"])

    if "fields" in data:
        for field in data["fields"]:
            if "inline" not in field or field["inline"]:
                inline = True
            else:
                inline = False

            if "name" in field and field["name"] != "" and field["name"] is not None:
                name = field["name"]
            else:
                name = empty

            if "value" in field and field["value"] != "" and field["value"] is not None:
                value = field["value"]
            else:
                value = empty

            embed.add_field(name=name, value=value, inline=inline)

    if "footer" in data and data["footer"] != {} and data["footer"] is not None:
        if "text" in data["footer"] and data["footer"]["text"] != "" and data["footer"]["text"] is not None:
            text = data["footer"]["text"]
        else:
            text = empty

        if "icon_url" in data["footer"] and data["footer"]["icon_url"] != "" and data["footer"]["icon_url"] is not None:
            icon_url = data["footer"]["icon_url"]
        else:
            icon_url = empty

        if icon_url != empty or text != empty:
            embed.set_footer(text=text, icon_url=icon_url)

    return embed
