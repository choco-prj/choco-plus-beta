from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
import requests
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'choco-tube-dev-key')
CORS(app)

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

def search_youtube(query, page_token=None, proxy_type="img.youtube.com", search_type="video"):
    for key in YOUTUBE_API_KEYS:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type={search_type}&maxResults=20&key={key}"
        if page_token:
            url += f"&pageToken={page_token}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = []
                video_ids = []
                for item in data.get('items', []):
                    if search_type == "channel":
                        results.append({
                            'id': item['id']['channelId'],
                            'title': item['snippet']['title'],
                            'thumbnail': item['snippet']['thumbnails']['default']['url'],
                            'type': 'channel',
                            'description': item['snippet']['description']
                        })
                    else:
                        v_id = item['id']['videoId']
                        video_ids.append(v_id)
                        results.append({
                            'id': v_id,
                            'title': item['snippet']['title'],
                            'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                            'channel': item['snippet']['channelTitle'],
                            'channel_id': item['snippet']['channelId'],
                            'type': 'video',
                            'views': 'N/A',
                            'published_at': item['snippet']['publishedAt']
                        })
                
                # Fetch video statistics to get view count
                if video_ids and search_type == "video":
                    try:
                        stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={','.join(video_ids)}&key={key}"
                        stats_response = requests.get(stats_url, timeout=5)
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            stats_map = {item['id']: item['statistics'].get('viewCount', '0') for item in stats_data.get('items', [])}
                            for result in results:
                                if result['type'] == 'video':
                                    view_count = int(stats_map.get(result['id'], 0))
                                    if view_count >= 1000000:
                                        result['views'] = f"{view_count/1000000:.1f}M"
                                    elif view_count >= 1000:
                                        result['views'] = f"{view_count/1000:.1f}K"
                                    else:
                                        result['views'] = str(view_count)
                    except Exception as e:
                        print(f"Error fetching video stats: {e}")
                
                return results, data.get('nextPageToken')
        except Exception as e:
            print(f"YouTube API error with key {key[:10]}...: {e}")
            continue
    print(f"All YouTube API keys failed for query: {query}")
    return None, None

def search_invidious(query, page=1, proxy_type="img.youtube.com", search_type="video"):
    instances = INVIDIOUS_INSTANCES.copy()
    random.shuffle(instances)
    for instance in instances:
        url = f"{instance}/api/v1/search?q={query}&type={search_type}&page={page}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data:
                    if search_type == "channel":
                        results.append({
                            'id': item['authorId'],
                            'title': item['author'],
                            'thumbnail': item.get('authorThumbnails', [{}])[0].get('url', ''),
                            'type': 'channel',
                            'description': item.get('description', '')
                        })
                    else:
                        v_id = item['videoId']
                        published_at = item.get('publishedText', '')
                        view_count = item.get('viewCount', 0)
                        if view_count >= 1000000:
                            views = f"{view_count/1000000:.1f}M"
                        elif view_count >= 1000:
                            views = f"{view_count/1000:.1f}K"
                        else:
                            views = str(view_count)
                        results.append({
                            'id': v_id,
                            'title': item['title'],
                            'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                            'channel': item['author'],
                            'channel_id': item.get('authorId', ''),
                            'type': 'video',
                            'views': views,
                            'published_at': published_at
                        })
                return results, page + 1
        except Exception as e:
            print(f"Invidious error {instance}: {e}")
            continue
    print(f"All Invidious instances failed for query: {query}")
    return None, None

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
    search_type = request.cookies.get('search_type', 'video')
    
    if not query:
        response = make_response(render_template('search.html', results=[], query="", proxy_type=proxy_type, mode=mode, search_type=search_type))
        response.set_cookie('proxy_type', proxy_type, max_age=2592000)
        response.set_cookie('search_mode', mode, max_age=2592000)
        response.set_cookie('search_type', search_type, max_age=2592000)
        return response
    
    results = None
    next_page = None
    
    if mode == 'inv_first':
        results, next_page = search_invidious(query, page, proxy_type, search_type)
        if not results:
            results, next_page = search_youtube(query, token, proxy_type, search_type)
    else:
        results, next_page = search_youtube(query, token, proxy_type, search_type)
        if not results:
            results, next_page = search_invidious(query, page, proxy_type, search_type)
    
    response = make_response(render_template('search.html', results=results if results else [], query=query, mode=mode, next_page=next_page, page=page, proxy_type=proxy_type, search_type=search_type))
    response.set_cookie('proxy_type', proxy_type, max_age=2592000)
    response.set_cookie('search_mode', mode, max_age=2592000)
    response.set_cookie('search_type', search_type, max_age=2592000)
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
    region = request.cookies.get('trend_region', 'JP')
    proxy_type = request.cookies.get('proxy_type', 'self-hosted')
    jp_category = request.cookies.get('trend_category', 'all')
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
    flask_response.set_cookie('trend_region', region, max_age=2592000)
    flask_response.set_cookie('trend_category', jp_category, max_age=2592000)
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

@app.route('/channel/<channel_id>')
def channel(channel_id):
    proxy_type = request.cookies.get('proxy_type', 'self-hosted')
    
    channel_name = "Unknown"
    subscriber_count = None
    video_count = None
    view_count = None
    description = None
    channel_image = None
    videos = []
    
    try:
        channel_data = None
        channel_source = None
        
        # Try YouTube API first
        for key in YOUTUBE_API_KEYS:
            try:
                url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={key}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        channel_data = data['items'][0]
                        channel_source = 'youtube'
                        break
            except Exception as e:
                print(f"Error fetching channel info: {e}")
                continue
        
        # Fallback to Invidious if YouTube API fails
        if not channel_data:
            instances = INVIDIOUS_INSTANCES.copy()
            random.shuffle(instances)
            for instance in instances:
                try:
                    url = f"{instance}/api/v1/channels/{channel_id}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        channel_data = response.json()
                        channel_source = 'invidious'
                        break
                except Exception as e:
                    print(f"Invidious channel error: {e}")
                    continue
        
        # Fetch videos
        for key in YOUTUBE_API_KEYS:
            try:
                url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&type=video&maxResults=20&key={key}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        try:
                            v_id = item['id']['videoId']
                            videos.append({
                                'id': v_id,
                                'title': item['snippet']['title'],
                                'thumbnail': get_proxy_thumbnail(v_id, proxy_type)
                            })
                        except KeyError as e:
                            print(f"Error parsing video item: {e}")
                            continue
                    break
            except Exception as e:
                print(f"Error fetching channel videos: {e}")
                continue
        
        # If YouTube API videos fetch failed, try Invidious
        if not videos and channel_source:
            instances = INVIDIOUS_INSTANCES.copy()
            random.shuffle(instances)
            for instance in instances:
                try:
                    url = f"{instance}/api/v1/channels/{channel_id}/latest"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        for item in data:
                            try:
                                v_id = item.get('videoId')
                                if v_id:
                                    videos.append({
                                        'id': v_id,
                                        'title': item.get('title', 'Unknown'),
                                        'thumbnail': get_proxy_thumbnail(v_id, proxy_type)
                                    })
                            except Exception as e:
                                print(f"Error parsing invidious video: {e}")
                                continue
                        break
                except Exception as e:
                    print(f"Invidious videos error: {e}")
                    continue
        
        # Process channel data
        if channel_data:
            if channel_source == 'youtube':
                try:
                    if 'snippet' in channel_data:
                        channel_name = channel_data['snippet'].get('title', 'Unknown')
                        description = channel_data['snippet'].get('description', '')
                        thumbnails = channel_data['snippet'].get('thumbnails', {})
                        if thumbnails:
                            channel_image = thumbnails.get('high', {}).get('url') or thumbnails.get('default', {}).get('url')
                    
                    if 'statistics' in channel_data:
                        sub_count = channel_data['statistics'].get('subscriberCount')
                        if sub_count:
                            sub_val = int(sub_count)
                            if sub_val >= 1000000:
                                subscriber_count = f"{sub_val/1000000:.1f}M"
                            elif sub_val >= 1000:
                                subscriber_count = f"{sub_val/1000:.1f}K"
                            else:
                                subscriber_count = str(sub_val)
                        
                        vid_count = channel_data['statistics'].get('videoCount')
                        if vid_count:
                            video_count = f"{int(vid_count):,}"
                        
                        view = channel_data['statistics'].get('viewCount')
                        if view:
                            view_val = int(view)
                            if view_val >= 1000000000:
                                view_count = f"{view_val/1000000000:.1f}B"
                            elif view_val >= 1000000:
                                view_count = f"{view_val/1000000:.1f}M"
                            else:
                                view_count = str(view_val)
                except Exception as e:
                    print(f"Error processing YouTube channel data: {e}")
            
            elif channel_source == 'invidious':
                try:
                    channel_name = channel_data.get('author', 'Unknown')
                    description = channel_data.get('description', '')
                    thumbnails = channel_data.get('authorThumbnails', [])
                    if thumbnails:
                        channel_image = thumbnails[0].get('url')
                    
                    sub_count = channel_data.get('subCount')
                    if sub_count:
                        sub_val = int(sub_count)
                        if sub_val >= 1000000:
                            subscriber_count = f"{sub_val/1000000:.1f}M"
                        elif sub_val >= 1000:
                            subscriber_count = f"{sub_val/1000:.1f}K"
                        else:
                            subscriber_count = str(sub_val)
                    
                    vid_count = channel_data.get('videoCount')
                    if vid_count:
                        video_count = f"{int(vid_count):,}"
                except Exception as e:
                    print(f"Error processing Invidious channel data: {e}")
    
    except Exception as e:
        print(f"Unexpected error in channel route: {e}")
        import traceback
        traceback.print_exc()
    
    return render_template('channel.html', 
                          channel_name=channel_name,
                          subscriber_count=subscriber_count,
                          video_count=video_count,
                          view_count=view_count,
                          description=description,
                          channel_image=channel_image,
                          videos=videos)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
