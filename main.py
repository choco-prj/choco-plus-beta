from flask import Flask, render_template, request, jsonify, make_response
import requests
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'choco-tube-dev-key')

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
    elif proxy_type == "self-hosted":
        # Self-hosted proxy thumbnail method
        return f"/api/thumbnail/{video_id}"
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

@app.route('/api/suggestions')
def suggestions():
    """検索候補を返すAPI"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        # YouTube APIから検索候補を取得
        suggestions_list = []
        for key in YOUTUBE_API_KEYS:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults=10&key={key}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        title = item['snippet']['title']
                        if title and title not in suggestions_list:
                            suggestions_list.append(title)
                        if len(suggestions_list) >= 10:
                            break
                    break
            except:
                continue
        
        # 候補が見つからなければクエリそのものを返す
        if not suggestions_list:
            return jsonify([query])
        
        return jsonify(suggestions_list[:10])
    except Exception as e:
        print(f"Error fetching suggestions: {e}")
        return jsonify([query])

@app.route('/')
def index():
    # Get preferences from cookies or set defaults
    proxy_type = request.cookies.get('proxy_type', 'self-hosted')
    search_mode = request.cookies.get('search_mode', 'inv_first')
    
    response = make_response(render_template('index.html', proxy_type=proxy_type, search_mode=search_mode))
    
    # Set default cookies
    response.set_cookie('proxy_type', proxy_type, max_age=2592000)  # 30 days
    response.set_cookie('search_mode', search_mode, max_age=2592000)  # 30 days
    
    return response

@app.route('/search')
def search():
    query = request.args.get('q', '')
    mode = request.cookies.get('search_mode', 'inv_first')
    page = request.args.get('page', 1, type=int)
    token = request.args.get('token', None)
    proxy_type = request.cookies.get('proxy_type', 'self-hosted')
    
    if not query:
        response = make_response(render_template('search.html', results=[], query="", proxy_type=proxy_type, mode=mode))
        response.set_cookie('proxy_type', proxy_type, max_age=2592000)
        response.set_cookie('search_mode', mode, max_age=2592000)
        return response
    
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
    
    response = make_response(render_template('search.html', results=results if results else [], query=query, mode=mode, next_page=next_page, page=page, proxy_type=proxy_type))
    response.set_cookie('proxy_type', proxy_type, max_age=2592000)
    response.set_cookie('search_mode', mode, max_age=2592000)
    return response

def get_japan_trend_by_category(category='all', proxy_type='self-hosted'):
    """
    日本トレンドをカテゴリ別に取得します
    
    Args:
        category: 'all' (全て), 'game' (ゲーム), 'music' (音楽)
        proxy_type: サムネイルプロキシの種類
    
    Returns:
        トレンド動画のリスト
    """
    results = []
    
    try:
        if category == 'all':
            # 全てカテゴリ: wakameリポジトリから取得
            url = "https://raw.githubusercontent.com/siawaseok3/wakame/refs/heads/master/trend.json"
        else:
            # ゲーム・音楽: ajgpwリポジトリから取得
            url = "https://raw.githubusercontent.com/ajgpw/youtubedata/refs/heads/main/trend-base64.json"
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # カテゴリ別に対応するキーを決定
            if category == 'all':
                # wakameリポジトリの場合は'trending'キーを使用
                trending_list = data.get('trending', data) if isinstance(data, dict) else data
            elif category == 'game':
                # ajgpwリポジトリのgamingキーを使用
                trending_list = data.get('gaming', [])
            elif category == 'music':
                # ajgpwリポジトリのmusicキーを使用
                trending_list = data.get('music', [])
            else:
                # デフォルト
                trending_list = data.get('trending', data) if isinstance(data, dict) else data
            
            for item in trending_list:
                v_id = item.get('id') or item.get('videoId')
                if not v_id: continue
                
                results.append({
                    'id': v_id,
                    'title': item.get('title') or 'No Title',
                    'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                    'channel': item.get('channel') or item.get('author') or item.get('channelTitle') or item.get('uploader') or 'Unknown'
                })
    except Exception as e:
        print(f"Error fetching JP trend (category={category}): {e}")
        pass
    
    return results

@app.route('/trend')
def trend():
    region = request.args.get('region', 'JP')
    proxy_type = request.args.get('proxy', request.cookies.get('proxy_type', 'self-hosted'))
    jp_category = request.args.get('jp_category', 'all')  # 日本トレンドカテゴリ（全て・ゲーム・音楽）
    results = []
    
    if region == 'JP':
        results = get_japan_trend_by_category(jp_category, proxy_type)
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
    
    flask_response = make_response(render_template('trend.html', results=results, region=region, proxy_type=proxy_type, jp_category=jp_category))
    flask_response.set_cookie('proxy_type', proxy_type, max_age=2592000)
    return flask_response

@app.route('/api/thumbnail/<video_id>')
def proxy_thumbnail(video_id):
    """Self-hosted proxy thumbnail - fetches from YouTube and serves locally"""
    try:
        url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.content, 200, {'Content-Type': response.headers.get('Content-Type', 'image/jpeg')}
    except:
        pass
    # Fallback to 1x1 transparent pixel if fetch fails
    return bytes.fromhex('47494638396101000100800000FFFFFF00000021F90400000000002C00000000010001000002024401003B'), 200, {'Content-Type': 'image/gif'}

@app.route('/watch/<video_id>')
def watch(video_id):
    return render_template('watch.html', video_id=video_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
