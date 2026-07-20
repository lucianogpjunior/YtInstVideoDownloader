import os
import re
import shutil
import tempfile

import yt_dlp

from flask import (
    Flask,
    after_this_request,
    redirect,
    render_template,
    request,
    send_file,
    url_for
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)


def plataforma(url):
    youtube = r"(youtube\.com|youtu\.be)"
    instagram = r"instagram\.com"

    if re.search(youtube, url, re.IGNORECASE):
        return "youtube"

    if re.search(instagram, url, re.IGNORECASE):
        return "instagram"

    return "desconhecido"


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        url = request.form.get("link")

        if url:

            return redirect(
                url_for(
                    "download",
                    url=url
                )
            )

    return render_template("index.html")


@app.route("/download")
def download():

    url = request.args.get("url")

    if not url:
        return "URL inválida", 400

    temp_dir = tempfile.mkdtemp()

    ydl_opts = {

        # melhor vídeo disponível
        "format": "best",

        # pasta temporária
        "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),

        # evita playlist
        "noplaylist": True,

        "quiet": True,

        "no_warnings": True,

        # navegador usado para burlar alguns bloqueios
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }

    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

            # procura o arquivo real
            for arquivo in os.listdir(temp_dir):

                filename = os.path.join(temp_dir, arquivo)

                break

        @after_this_request
        def remover(response):

            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(e)

            return response

        return send_file(
            filename,
            as_attachment=True,
            download_name=os.path.basename(filename)
        )

    except Exception as e:

        shutil.rmtree(temp_dir, ignore_errors=True)

        return f"""
        <h2>Erro ao baixar o vídeo.</h2>
        <pre>{e}</pre>
        """, 400


if __name__ == "__main__":
    app.run(debug=True)