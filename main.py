from flask import Flask, render_template, request, jsonify
import requests
import random
import os

app = Flask(__name__)

YOUTUBE_API_KEYS = [
    "AIzaSyBQ-40ld7erVfx7s6iKBYl-GjDqJVYBwrc",
    "AIzaSyCoz9NrmBu5mFRm_-qD4XoTFaqu7AGvGeU",
    "AIzaSyDdgsY60mxo98j99leqp1pb5aFYvSSvrSc",
    "AIzaSyC__tVvRkEHBtGIjfxhD_FbG3fAcjiaXlc",
    "AIzaSyAZwLva1HxzDbKFJuE9RVcxS5B4q_ol8yE",
    "AIzaSyCqvGnAlX4_Ss7PInUEg3RWucbdjmnWP6U",
    "AIzaSyBw0JamBkR5eOJLYnmBBxEoptlVm22Q0oA",
    "AIzaSyCz7f0X_giaGyC9u1EfGZPBuAC9nXiL5Mo",
    "AIzaSyBmzCw7-sX1vm-uL_u2Qy3LuVZuxye4Wys",
    "AIzaSyBWScla0K91jUL6qQErctN9N2b3j9ds7HI",
    "AIzaSyA17CdOQtQRC3DQe7rgIzFwTUjwAy_3CAc",
    "AIzaSyDdk_yY0tN4gKsm4uyMYrIlv1RwXIYXrnw",
    "AIzaSyDeU5zpcth2OgXDfToyc7-QnSJsDc41UGk",
    "AIzaSyClu2V_22XpCG2GTe1euD35_Mh5bn4eTjA"
]

INVIDIOUS_INSTANCES = [
    "https://yt.omada.cafe",
    "https://invidious.lunivers.trade",
    "https://invidious.ritoge.com",
    "https://super8.absturztau.be",
    "https://invidious.f5.si",
    "https://lekker.gay",
    "https://iv.melmac.space",
    "https://invidious.vern.cc",
    "https://yt.vern.cc",
    "https://inv.kamuridesu.com",
    "https://inv.thepixora.com",
    "https://invidious.tiekoetter.com",
    "https://youtube.mosesmang.com",
    "https://invidious.ducks.party",
    "https://inv.zoomerville.com",
    "https://invidious.materialio.us",
    "https://inv.nadeko.net",
    "https://yt.thechangebook.org",
    "https://y.com.sb",
    "https://invidious.reallyaweso.me",
    "https://invidious.dhusch.de"
]

def get_proxy_thumbnail(video_id, proxy_type="img.youtube.com"):
    if proxy_type == "i.ytimg.com":
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

def search_youtube(query, page_token=None, proxy_type="img.youtube.com"):
    for key in YOUTUBE_API_KEYS:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults=20&key={key}"
        if page_token:
            url += f"&pageToken={page_token}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('items', []):
                    v_id = item['id']['videoId']
                    results.append({
                        'id': v_id,
                        'title': item['snippet']['title'],
                        'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                        'channel': item['snippet']['channelTitle']
                    })
                return results, data.get('nextPageToken')
        except:
            continue
    return None, None

def search_invidious(query, page=1, proxy_type="img.youtube.com"):
    instances = INVIDIOUS_INSTANCES.copy()
    random.shuffle(instances)
    for instance in instances:
        url = f"{instance}/api/v1/search?q={query}&type=video&page={page}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data:
                    v_id = item['videoId']
                    results.append({
                        'id': v_id,
                        'title': item['title'],
                        'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                        'channel': item['author']
                    })
                return results, page + 1
        except:
            continue
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    mode = request.args.get('mode', 'inv_first')
    page = request.args.get('page', 1, type=int)
    token = request.args.get('token', None)
    proxy_type = request.args.get('proxy', 'img.youtube.com')
    
    if not query:
        return render_template('search.html', results=[], query="", proxy_type=proxy_type)
    
    results = None
    next_page = None
    
    if mode == 'inv_first':
        results, next_page = search_invidious(query, page, proxy_type)
        if not results:
            results, next_page = search_youtube(query, token, proxy_type)
    else:
        results, next_page = search_youtube(query, token, proxy_type)
        if not results:
            results, next_page = search_invidious(query, page, proxy_type)
        
    return render_template('search.html', results=results if results else [], query=query, mode=mode, next_page=next_page, page=page, proxy_type=proxy_type)

@app.route('/trend')
def trend():
    region = request.args.get('region', 'JP')
    proxy_type = request.args.get('proxy', 'img.youtube.com')
    results = []
    
    if region == 'JP':
        try:
            url = "https://raw.githubusercontent.com/siawaseok3/wakame/refs/heads/master/trend.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    v_id = item.get('videoId') or item.get('id')
                    if not v_id: continue
                    results.append({
                        'id': v_id,
                        'title': item.get('title') or 'No Title',
                        'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                        'channel': item.get('author') or item.get('channelTitle') or item.get('uploader') or 'Unknown'
                    })
        except Exception as e:
            print(f"Error fetching JP trend: {e}")
            pass
    else:
        instances = INVIDIOUS_INSTANCES.copy()
        random.shuffle(instances)
        for instance in instances:
            url = f"{instance}/api/v1/trending?region={region}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    for item in data:
                        v_id = item['videoId']
                        results.append({
                            'id': v_id,
                            'title': item['title'],
                            'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                            'channel': item['author']
                        })
                    break
            except:
                continue
                
    return render_template('trend.html', results=results, region=region, proxy_type=proxy_type)

@app.route('/watch/<video_id>')
def watch(video_id):
    return render_template('watch.html', video_id=video_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
