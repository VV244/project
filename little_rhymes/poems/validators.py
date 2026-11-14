import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.exceptions import ValidationError

def image_upload_path(instance, filename):
    return f'images/{uuid4().hex}{Path(filename).suffix.lower()}'

def audio_upload_path(instance, filename):
    return f'audio/{uuid4().hex}.mp3'

def validate_image(file):
    if file.size > 5 * 1024 * 1024:
        raise ValidationError('Images must be smaller than 5 MB.')
    if Path(file.name).suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
        raise ValidationError('Upload a JPEG, PNG or WebP image. SVG uploads are not accepted.')
    try:
        file.seek(0)
        with Image.open(file) as image:
            if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 16_000_000:
                raise ValidationError('Image must be a supported format and at most 16 megapixels.')
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError('This image is invalid or too large.')
    finally:
        file.seek(0)

def validate_audio(file):
    if file.size > 20 * 1024 * 1024:
        raise ValidationError('Audio must be smaller than 20 MB.')
    if Path(file.name).suffix.lower() != '.mp3':
        raise ValidationError('Upload an MP3 file.')
    file.seek(0)
    header = file.read(10)
    file.seek(0)
    # MP3 ID3 tag or MPEG audio frame; reject renamed HTML and executables.
    if not (header.startswith(b'ID3') or (len(header) >= 2 and header[0] == 255 and header[1] & 0xE0 == 0xE0)):
        raise ValidationError('The file does not have a valid MP3 header.')

def youtube_id(url):
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    if host == 'youtu.be':
        candidate = parsed.path.strip('/')
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'www.youtube-nocookie.com'):
        parts = parsed.path.strip('/').split('/')
        candidate = parse_qs(parsed.query).get('v', [''])[0] if parsed.path == '/watch' else (parts[1] if len(parts) == 2 and parts[0] in ('embed', 'shorts') else '')
    else:
        return None
    return candidate if re.fullmatch(r'[A-Za-z0-9_-]{11}', candidate) else None

def validate_video_url(value):
    if not value:
        return
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError:
        raise ValidationError('Video URL has an invalid port.')
    if parsed.scheme != 'https' or parsed.username or parsed.password or port not in (None, 443):
        raise ValidationError('Video URLs must use HTTPS without credentials or custom ports.')
    if youtube_id(value):
        return
    if parsed.hostname in settings.EXTERNAL_VIDEO_HOSTS and parsed.path.lower().endswith(('.mp4', '.webm')):
        return
    raise ValidationError('Use a valid YouTube URL, or an MP4/WebM URL on an approved video host.')
