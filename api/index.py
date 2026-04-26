from pickle import GET
from flask import Flask, redirect, render_template, request, send_file, session, url_for
from pytubefix import Playlist
from pytubefix import YouTube
import requests
import instaloader
import io
import re

app = Flask(__name__,
            template_folder="../templates", 
            static_folder="../static")
def ind_plataforma(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|shorts/|.+\?v=)?([^&=%\?]{11})'
    instagram_regex = r'(https?://)?(www\.)?instagram\.com/(p|reels|tv)/([^/?#&]+)'
    plataforma = ""

    if re.search(youtube_regex, url):
        plataforma = "yt"
        return plataforma
    elif re.search(instagram_regex, url):
        plataforma = "insta"
        return plataforma
    else:
        return "desconhecido" 

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        url = request.form.get("link")
        
        if url:
            plataforma = ind_plataforma(url)
            return redirect(url_for('videoDownload', url = url, plataforma = plataforma))
    return render_template('index.html')

@app.route("/download")
def videoDownload():
        url = request.args.get("url")
        plataforma = request.args.get("plataforma")

        if (plataforma == "yt"):
            
            yt = YouTube(
                url,
                use_oauth=False, 
                allow_oauth_cache=True
            )
            stream = yt.streams.get_highest_resolution()

            buffer = io.BytesIO()
            stream.stream_to_buffer(buffer)
            buffer.seek(0)

            return send_file(buffer, 
                as_attachment=True,
                download_name=f"{yt.title}.mp4",
                mimetype="video/mp4"
                )
        
        elif (plataforma == "insta"):
            loader = instaloader.Instaloader(
                download_comments= False,
                download_geotags= False,
                download_pictures= False,
                download_video_thumbnails= False,
                save_metadata= False
            )
            shortcode = url.split('/')[-2]
            try:
                post = instaloader.Post.from_shortcode(loader.context, shortcode)
                
                if post.is_video:
                    video_url = post.video_url
                    res = requests.get(video_url, stream=True)
                    
                    buffer = io.BytesIO(res.content)
                    buffer.seek(0)

                    titulo = (post.caption[:30] if post.caption else shortcode)
                    nome_arquivo = f"{titulo}.mp4"

                    return send_file(
                        buffer,
                        as_attachment=True,
                        download_name=nome_arquivo,
                        mimetype="video/mp4"
                    )
            except Exception as e:
                print(f"Erro no Insta: {e}")
                return "Erro ao processar vídeo do Instagram", 400

'''
@app.route("/playlist")
def playlist_view():
    url = 'https://www.youtube.com/playlist?list=PLltybNbFtZ8ZkgbG44_rpMVx3pg_hWIcR'
    result = videosInPlaylist.functionLink(url)
    return render_template('index.html', videos_template=result)


class videosInPlaylist:
    @staticmethod
    def functionLink(url):
        pl = Playlist(url)
        try:
            videos = []
            for video in pl.videos:
                videos.append({
                    "titulo": video.title,
                    "url": video.watch_url,
                    "thumbnail": video.thumbnail_url
                            })
            return videos
        except Exception as error:
            return "Erro, não foi possivel encontrar a playlist"
'''       
#if __name__ == '__main__':
#       app.run(debug=True)


