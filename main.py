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

def parse_iso8601_duration(duration_str):
    """Parse ISO 8601 duration (e.g., PT1H23M45S) to readable format (1:23:45 or 23:45)"""
    if not duration_str:
        return ""
    try:
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if match:
            hours, minutes, seconds = match.groups()
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0
            
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        return ""
    except:
        return ""

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
                            'published_at': item['snippet']['publishedAt'],
                            'duration': ''
                        })
                
                # Fetch video statistics and duration to get view count and length
                if video_ids and search_type == "video":
                    try:
                        stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&id={','.join(video_ids)}&key={key}"
                        stats_response = requests.get(stats_url, timeout=5)
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            stats_map = {item['id']: item for item in stats_data.get('items', [])}
                            for result in results:
                                if result['type'] == 'video' and result['id'] in stats_map:
                                    item = stats_map[result['id']]
                                    view_count = int(item.get('statistics', {}).get('viewCount', 0))
                                    if view_count >= 1000000:
                                        result['views'] = f"{view_count/1000000:.1f}M"
                                    elif view_count >= 1000:
                                        result['views'] = f"{view_count/1000:.1f}K"
                                    else:
                                        result['views'] = str(view_count)
                                    
                                    duration = item.get('contentDetails', {}).get('duration', '')
                                    result['duration'] = parse_iso8601_duration(duration)
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
    date_format = request.cookies.get('date_format', 'ago')
    
    if not query:
        response = make_response(render_template('search.html', results=[], query="", proxy_type=proxy_type, mode=mode, search_type=search_type, date_format=date_format))
        response.set_cookie('proxy_type', proxy_type, max_age=2592000)
        response.set_cookie('search_mode', mode, max_age=2592000)
        response.set_cookie('search_type', search_type, max_age=2592000)
        response.set_cookie('date_format', date_format, max_age=2592000)
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
    
    response = make_response(render_template('search.html', results=results if results else [], query=query, mode=mode, next_page=next_page, page=page, proxy_type=proxy_type, search_type=search_type, date_format=date_format))
    response.set_cookie('proxy_type', proxy_type, max_age=2592000)
    response.set_cookie('search_mode', mode, max_age=2592000)
    response.set_cookie('search_type', search_type, max_age=2592000)
    response.set_cookie('date_format', date_format, max_age=2592000)
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
            
            video_ids = []
            for item in trending_list:
                v_id = item.get('id') or item.get('videoId')
                if not v_id: continue
                video_ids.append(v_id)
                
                published = item.get('published') or item.get('publishedAt') or item.get('uploadedAt') or ''
                results.append({
                    'id': v_id,
                    'title': item.get('title') or 'No Title',
                    'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                    'channel': item.get('channel') or item.get('author') or item.get('channelTitle') or item.get('uploader') or 'Unknown',
                    'duration': '',
                    'views': 'N/A',
                    'published_at': published
                })
            
            # Fetch duration and view count from YouTube API
            if video_ids:
                for key in YOUTUBE_API_KEYS:
                    try:
                        stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails,statistics&id={','.join(video_ids[:50])}&key={key}"
                        stats_response = requests.get(stats_url, timeout=5)
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            stats_map = {item['id']: item for item in stats_data.get('items', [])}
                            for result in results:
                                if result['id'] in stats_map:
                                    item = stats_map[result['id']]
                                    duration = item.get('contentDetails', {}).get('duration', '')
                                    result['duration'] = parse_iso8601_duration(duration)
                                    
                                    # Check if live
                                    is_live = item.get('contentDetails', {}).get('projection', None) == 'live'
                                    if is_live:
                                        result['duration'] = 'LIVE'
                                    
                                    view_count = int(item.get('statistics', {}).get('viewCount', 0))
                                    if view_count >= 1000000:
                                        result['views'] = f"{view_count/1000000:.1f}M"
                                    elif view_count >= 1000:
                                        result['views'] = f"{view_count/1000:.1f}K"
                                    else:
                                        result['views'] = str(view_count)
                            break
                    except Exception as e:
                        print(f"Error fetching JP trend stats: {e}")
                        continue
    except Exception as e:
        print(f"Error fetching JP trend (category={category}): {e}")
        pass
    
    return results

@app.route('/trend')
def trend():
    region = request.cookies.get('trend_region', 'JP')
    proxy_type = request.cookies.get('proxy_type', 'self-hosted')
    date_format = request.cookies.get('date_format', 'ago')
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
                    video_ids = []
                    for item in data:
                        v_id = item['videoId']
                        video_ids.append(v_id)
                        
                        # Try to get duration from Invidious response first
                        duration = ''
                        if 'lengthSeconds' in item:
                            duration = format_time_seconds(int(item.get('lengthSeconds', 0)))
                        
                        results.append({
                            'id': v_id,
                            'title': item['title'],
                            'thumbnail': get_proxy_thumbnail(v_id, proxy_type),
                            'channel': item['author'],
                            'duration': duration,
                            'views': 'N/A',
                            'published_at': item.get('uploadedAt', '')
                        })
                    
                    # Fetch duration and view count from YouTube API
                    if video_ids:
                        for key in YOUTUBE_API_KEYS:
                            try:
                                stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails,statistics&id={','.join(video_ids[:50])}&key={key}"
                                stats_response = requests.get(stats_url, timeout=5)
                                if stats_response.status_code == 200:
                                    stats_data = stats_response.json()
                                    stats_map = {item['id']: item for item in stats_data.get('items', [])}
                                    for result in results:
                                        if result['id'] in stats_map:
                                            item = stats_map[result['id']]
                                            duration = item.get('contentDetails', {}).get('duration', '')
                                            # Only update duration if not already set from Invidious
                                            if not result['duration'] and duration:
                                                result['duration'] = parse_iso8601_duration(duration)
                                            
                                            view_count = int(item.get('statistics', {}).get('viewCount', 0))
                                            if view_count >= 1000000:
                                                result['views'] = f"{view_count/1000000:.1f}M"
                                            elif view_count >= 1000:
                                                result['views'] = f"{view_count/1000:.1f}K"
                                            else:
                                                result['views'] = str(view_count)
                                    break
                            except Exception as e:
                                print(f"Error fetching trend stats: {e}")
                                continue
                    break
            except:
                continue
    
    flask_response = make_response(render_template('trend.html', results=results, region=region, proxy_type=proxy_type, date_format=date_format, jp_category=jp_category))
    flask_response.set_cookie('proxy_type', proxy_type, max_age=2592000)
    flask_response.set_cookie('date_format', date_format, max_age=2592000)
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

def format_view_count(count):
    if isinstance(count, str):
        try:
            count = int(count)
        except:
            return count
    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.1f}K"
    return str(count)

def parse_duration_to_seconds(duration_str):
    """Parse ISO 8601 duration to seconds"""
    if not duration_str:
        return 0
    try:
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if match:
            hours, minutes, seconds = match.groups()
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0
            return hours * 3600 + minutes * 60 + seconds
        return 0
    except:
        return 0

def format_time_seconds(seconds):
    """Format seconds to MM:SS or H:MM:SS"""
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    except:
        return ""

def format_date_with_cookie(iso_date_str, date_format=None):
    """Format ISO 8601 date based on cookie preference or parameter"""
    if not iso_date_str:
        return ""
    try:
        from datetime import datetime
        # Parse ISO 8601 format
        if 'T' in iso_date_str:
            dt = datetime.fromisoformat(iso_date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(iso_date_str)
        
        # If format not specified, default to 'ago'
        if date_format is None:
            date_format = 'ago'
        
        # YYYY-MM-DD format
        if date_format == 'date':
            return dt.strftime('%Y-%m-%d')
        
        # ~ago format (default)
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.utcnow()
        delta = now - dt
        days = delta.days
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return "now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif days == 0:
            return "today"
        elif days == 1:
            return "1 day ago"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    except:
        return iso_date_str[:10] if len(iso_date_str) >= 10 else iso_date_str

def format_relative_date(iso_date_str):
    """Format ISO 8601 date to relative time format (for backward compatibility)"""
    return format_date_with_cookie(iso_date_str, 'ago')

def get_video_details(video_id, key):
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&id={video_id}&key={key}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                item = data['items'][0]
                view_count = item.get('statistics', {}).get('viewCount', '0')
                duration = item.get('contentDetails', {}).get('duration', '')
                return {
                    'views': format_view_count(view_count),
                    'duration': duration
                }
    except:
        pass
    return {'views': '0', 'duration': ''}

@app.route('/channel/<channel_id>')
def channel(channel_id):
    channel = None
    all_videos = []
    videos = []
    shorts = []
    
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
        
        # Fetch videos using uploads playlist
        uploads_playlist_id = None
        if channel_source == 'youtube' and channel_data:
            uploads_playlist_id = f"UU{channel_id[2:]}"
        
        for key in YOUTUBE_API_KEYS:
            try:
                if uploads_playlist_id:
                    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=50&key={key}"
                else:
                    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&type=video&order=date&maxResults=50&key={key}"
                
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    video_ids = []
                    for item in data.get('items', []):
                        try:
                            if 'playlistItems' in url:
                                v_id = item['snippet']['resourceId']['videoId']
                            else:
                                v_id = item['id']['videoId']
                            video_ids.append(v_id)
                            all_videos.append({
                                'id': v_id,
                                'title': item['snippet']['title'],
                                'published': item['snippet']['publishedAt'][:10] if 'publishedAt' in item['snippet'] else '',
                                'views': '0',
                                'length': '',
                                'is_short': False
                            })
                        except KeyError as e:
                            print(f"Error parsing video item: {e}")
                            continue
                    
                    # Fetch video details to get duration and statistics
                    if video_ids:
                        try:
                            details_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails,statistics&id={','.join(video_ids)}&key={key}"
                            details_response = requests.get(details_url, timeout=5)
                            if details_response.status_code == 200:
                                details_data = details_response.json()
                                details_map = {item['id']: item for item in details_data.get('items', [])}
                                for video in all_videos:
                                    if video['id'] in details_map:
                                        duration_str = details_map[video['id']].get('contentDetails', {}).get('duration', '')
                                        video['length'] = parse_iso8601_duration(duration_str)
                                        # Check if it's a short (duration <= 60 seconds)
                                        duration = parse_duration_to_seconds(duration_str)
                                        video['is_short'] = duration <= 60
                                        # Get view count
                                        view_count = details_map[video['id']].get('statistics', {}).get('viewCount', '0')
                                        video['views'] = format_view_count(view_count)
                        except Exception as e:
                            print(f"Error fetching video details: {e}")
                    break
            except Exception as e:
                print(f"Error fetching channel videos: {e}")
                continue
        
        # If YouTube API videos fetch failed, try Invidious
        if not all_videos and channel_source:
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
                                    view_count = item.get('viewCount', 0)
                                    length = item.get('lengthSeconds', 0)
                                    all_videos.append({
                                        'id': v_id,
                                        'title': item.get('title', 'Unknown'),
                                        'published': item.get('published', ''),
                                        'views': format_view_count(view_count),
                                        'length': format_time_seconds(length),
                                        'is_short': int(length) <= 60
                                    })
                            except Exception as e:
                                print(f"Error parsing invidious video: {e}")
                                continue
                        break
                except Exception as e:
                    print(f"Invidious videos error: {e}")
                    continue
        
        # Separate videos and shorts
        for video in all_videos:
            if video['is_short']:
                shorts.append(video)
            else:
                videos.append(video)
        
        # Process channel data
        if channel_data:
            channel = {}
            if channel_source == 'youtube':
                try:
                    if 'snippet' in channel_data:
                        channel['channelName'] = channel_data['snippet'].get('title', 'Unknown')
                        channel['channelProfile'] = channel_data['snippet'].get('description', '')
                        thumbnails = channel_data['snippet'].get('thumbnails', {})
                        if thumbnails:
                            channel['channelIcon'] = thumbnails.get('high', {}).get('url') or thumbnails.get('default', {}).get('url')
                    
                    if 'statistics' in channel_data:
                        sub_count = channel_data['statistics'].get('subscriberCount')
                        if sub_count:
                            channel['subscribers'] = int(sub_count)
                        
                        view = channel_data['statistics'].get('viewCount')
                        if view:
                            channel['totalViews'] = int(view)
                except Exception as e:
                    print(f"Error processing YouTube channel data: {e}")
            
            elif channel_source == 'invidious':
                try:
                    channel['channelName'] = channel_data.get('author', 'Unknown')
                    channel['channelProfile'] = channel_data.get('description', '')
                    thumbnails = channel_data.get('authorThumbnails', [])
                    if thumbnails:
                        channel['channelIcon'] = thumbnails[0].get('url')
                    
                    sub_count = channel_data.get('subCount')
                    if sub_count:
                        channel['subscribers'] = int(sub_count)
                except Exception as e:
                    print(f"Error processing Invidious channel data: {e}")
    
    except Exception as e:
        print(f"Unexpected error in channel route: {e}")
        import traceback
        traceback.print_exc()
    
    date_format = request.cookies.get('date_format', 'ago')
    return render_template('channel.html', channel=channel, videos=videos, shorts=shorts, date_format=date_format)

@app.route('/api/channel/<channel_id>/more')
def channel_more(channel_id):
    video_type = request.args.get('type', 'videos')
    offset = request.args.get('offset', 0, type=int)
    
    all_videos = []
    
    try:
        uploads_playlist_id = f"UU{channel_id[2:]}"
        
        for key in YOUTUBE_API_KEYS:
            try:
                url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=50&startIndex={offset+1}&key={key}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    video_ids = []
                    for item in data.get('items', []):
                        try:
                            v_id = item['snippet']['resourceId']['videoId']
                            video_ids.append(v_id)
                            all_videos.append({
                                'id': v_id,
                                'title': item['snippet']['title'],
                                'published': item['snippet']['publishedAt'][:10] if 'publishedAt' in item['snippet'] else '',
                                'views': '0',
                                'length': '',
                                'is_short': False
                            })
                        except KeyError:
                            continue
                    
                    if video_ids:
                        try:
                            details_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={','.join(video_ids)}&key={key}"
                            details_response = requests.get(details_url, timeout=5)
                            if details_response.status_code == 200:
                                details_data = details_response.json()
                                details_map = {item['id']: item for item in details_data.get('items', [])}
                                for video in all_videos:
                                    if video['id'] in details_map:
                                        duration_str = details_map[video['id']].get('contentDetails', {}).get('duration', '')
                                        video['length'] = parse_iso8601_duration(duration_str)
                                        duration = parse_duration_to_seconds(duration_str)
                                        video['is_short'] = duration <= 60
                        except:
                            pass
                    break
            except Exception as e:
                print(f"Error fetching more videos: {e}")
                continue
        
        # Filter by type
        result_videos = []
        for video in all_videos:
            if video_type == 'videos' and not video['is_short']:
                result_videos.append(video)
            elif video_type == 'shorts' and video['is_short']:
                result_videos.append(video)
        
        return jsonify({'videos': result_videos})
    except Exception as e:
        print(f"Error in channel_more: {e}")
        return jsonify({'videos': []})

# Register Jinja2 filters
app.jinja_env.filters['format_relative_date'] = format_relative_date
app.jinja_env.filters['format_date'] = format_date_with_cookie

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
