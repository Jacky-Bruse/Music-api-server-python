from server.exceptions import FailedException
from server.models.music import SongInfo
from utils.platform import formatPlayTime
from utils.server import http as request


async def get_pic(songId: str | int, albumId: str | int) -> str:
    pic_url_req = await request.send_http_request(
        f"https://artistpicserver.kuwo.cn/pic.web?corp=kuwo&type=rid_pic&pictype=500&size=500&rid={songId}"
    )
    picUrl = pic_url_req.text

    if picUrl == "NO_PIC":
        pic_url_req = await request.send_http_request(
            f"https://searchlist.kuwo.cn/r.s?stype=albuminfo&albumid={albumId}&show_copyright_off=1&alflac=1&vipver=1&sortby=1&newver=1&mobi=1"
        )
        picUrl = pic_url_req.json().get("hts_img", "")

    return picUrl


async def getMusicInfo(songId: str | int) -> SongInfo:
    url = f"https://musicpay.kuwo.cn/music.pay?ver=MUSIC_9.1.1.2_BCS2&src=mbox&op=query&signver=new&action=play&ids={songId}&accttype=1&appuid=38668888"
    req = await request.send_http_request(url)

    if req.status_code != 200:
        raise FailedException(f"获取歌曲信息失败: {req.json()}")

    body = req.json()["songs"][0]
    pic = await get_pic(body["id"], body.get("albumid"))

    return SongInfo(
        songId=body.get("id"),
        songName=body.get("name"),
        artistName=body.get("artist"),
        albumName=body.get("album"),
        albumId=body.get("albumid"),
        duration=(
            formatPlayTime(body.get("duration"))
            if body.get("duration") is not None
            else None
        ),
        coverUrl=pic,
    )
