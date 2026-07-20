import io
import os
import re
import tempfile

import instaloader
import requests
import yt_dlp

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

# Caminho da raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)


def ind_plataforma(url):
    youtube_regex = (
        r"(https?://)?(www\.)?"
        r"(youtube|youtu|youtube-nocookie)\.(com|be)/"
        r"(watch\?v=|embed/|v/|shorts/|.+\?v=)?([^&=%\?]{11})"
    )

    instagram_regex = (
        r"(https?://)?(www\.)?"
        r"instagram\.com/(p|reel|reels|tv)/([^/?#&]+)"
    )

    if re.search(youtube_regex, url):
        return "yt"

    if re.search(instagram_regex, url):
        return "insta"

    return "desconhecido"


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        url = request.form.get("link")

        if url:

            plataforma = ind_plataforma(url)

            return redirect(
                url_for(
                    "videoDownload",
                    url=url,
                    plataforma=plataforma,
                )
            )

    return render_template("index.html")


@app.route("/download")
def videoDownload():

    url = request.args.get("url")
    plataforma = request.args.get("plataforma")

    if not url:
        return "URL não informada.", 400

    if plataforma == "yt":

        try:

            temp_dir = tempfile.mkdtemp()

            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "merge_output_format": "mp4",
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "quiet": True,
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(url, download=True)

                filename = ydl.prepare_filename(info)

            # yt-dlp pode trocar a extensão após unir vídeo+áudio
            base = os.path.splitext(filename)[0]

            if os.path.exists(base + ".mp4"):
                filename = base + ".mp4"

            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename),
                mimetype="video/mp4",
            )

        except Exception as e:

            print(e)

            return f"Erro ao baixar vídeo do YouTube:<br><br>{e}", 400

    elif plataforma == "insta":

        try:

            loader = instaloader.Instaloader(
                download_comments=False,
                download_geotags=False,
                download_pictures=False,
                download_video_thumbnails=False,
                save_metadata=False,
            )

            shortcode = url.split("/")[-2]

            post = instaloader.Post.from_shortcode(
                loader.context,
                shortcode,
            )

            if not post.is_video:
                return "Esse post não contém vídeo."

            response = requests.get(post.video_url)

            buffer = io.BytesIO(response.content)
            buffer.seek(0)

            titulo = post.caption[:30] if post.caption else shortcode

            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{titulo}.mp4",
                mimetype="video/mp4",
            )

        except Exception as e:

            print(e)

            return f"Erro ao baixar vídeo do Instagram:<br><br>{e}", 400

    return "URL inválida.", 400


if __name__ == "__main__":
    app.run(debug=True)