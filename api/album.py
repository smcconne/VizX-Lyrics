from api.lyrics import getLyrics

def album(data, syncpoints):
    info = {}
    attr = data["data"][0]["attributes"]

    name = attr["name"]
    artist_name = attr.get("artistName", "")

    if " - EP" in name:
        name = name.replace(" - EP", "") + " [EP]"
    if " - Single" in name:
        name = name.replace(" - Single", "") + " [S]"

    __dir = "{0} - {1} [{2}]".format(
        artist_name,
        name,
        data["data"][0]["id"]
    )

    if "contentRating" in attr:
        if attr["contentRating"] == "explicit":
            __dir += " [E]"

    info["dir"] = __dir
    info["artist_name"] = artist_name
    info["album_name"] = name

    if "artwork" in attr:
        info["coverUrl"] = attr["artwork"].get("url").format(
            w=attr["artwork"].get("width"),
            h=attr["artwork"].get("height")
        )

    trackList = []
    tracks = data["data"][0]["relationships"]["tracks"]["data"]

    for track in tracks:
        __info = {}
        __info["id"] = track.get("id")
        
        attr = track["attributes"]
        track_name = attr.get("name", "")
        track_artist = attr.get("artistName", artist_name)

        if track.get("type") == "songs":
            __file = "{0} - {1}".format(
                str(attr.get("trackNumber")).zfill(2),
                track_name
            )

            if "contentRating" in attr:
                if attr.get("contentRating") == "explicit":
                    __file += " [E]"

            __info["file"] = __file
            __info["name"] = track_name
            __info["artist"] = track_artist
            if "durationInMillis" in attr:
                __info["duration"] = attr.get("durationInMillis", 0) / 1000.0

            if "syllable-lyrics" in track.get("relationships", {}) and len(track["relationships"]["syllable-lyrics"].get("data", [])) > 0:
                __info["ttml"] = track["relationships"]["syllable-lyrics"]["data"][0]["attributes"].get("ttml")
                __info.update(getLyrics(__info["ttml"], syncpoints))
            elif "lyrics" in track.get("relationships", {}) and len(track["relationships"]["lyrics"].get("data", [])) > 0:
                __info["ttml"] = track["relationships"]["lyrics"]["data"][0]["attributes"].get("ttml")
                __info.update(getLyrics(__info["ttml"], syncpoints))

        trackList.append(__info)
        
    info["tracks"] = trackList

    return info