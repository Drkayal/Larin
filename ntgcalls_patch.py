"""
Compatibility patch for py-tgcalls 1.0.9 with ntgcalls 1.x/2.x
This patch creates aliases for StreamStatus attributes to maintain compatibility
and injects an InputMode shim expected by pytgcalls 1.0.9
"""

import ntgcalls

# Inject InputMode shim if missing in ntgcalls
if not hasattr(ntgcalls, 'InputMode'):
	class InputMode:  # minimal shim mapping to ntgcalls constants
		Shell = getattr(ntgcalls, 'SHELL', None)
		File = getattr(ntgcalls, 'FILE', None)
		FFmpeg = getattr(ntgcalls, 'FFMPEG', None)
		Capture = getattr(ntgcalls, 'CAPTURE', None)
		External = getattr(ntgcalls, 'EXTERNAL', None)
		Device = getattr(ntgcalls, 'DEVICE', None)
		Desktop = getattr(ntgcalls, 'DESKTOP', None)
		Camera = getattr(ntgcalls, 'CAMERA', None)
		Microphone = getattr(ntgcalls, 'MICROPHONE', None)

	setattr(ntgcalls, 'InputMode', InputMode)

# Create aliases for compatibility with py-tgcalls 1.0.9
if not hasattr(ntgcalls.StreamStatus, 'Playing'):
	if hasattr(ntgcalls.StreamStatus, 'ACTIVE'):
		ntgcalls.StreamStatus.Playing = ntgcalls.StreamStatus.ACTIVE
	elif hasattr(ntgcalls.StreamStatus, 'PLAYING'):
		ntgcalls.StreamStatus.Playing = ntgcalls.StreamStatus.PLAYING

if not hasattr(ntgcalls.StreamStatus, 'Paused'):
	if hasattr(ntgcalls.StreamStatus, 'PAUSED'):
		ntgcalls.StreamStatus.Paused = ntgcalls.StreamStatus.PAUSED

if not hasattr(ntgcalls.StreamStatus, 'Idling'):
	if hasattr(ntgcalls.StreamStatus, 'IDLING'):
		ntgcalls.StreamStatus.Idling = ntgcalls.StreamStatus.IDLING

# Wrap AudioDescription to accept legacy kwargs from py-tgcalls 1.0.9
try:
	_OrigAudioDescription = getattr(ntgcalls, 'AudioDescription', None)
	if _OrigAudioDescription is not None:
		_MS = getattr(ntgcalls, 'MediaSource', None)
		def _compat_AudioDescription(*args, **kwargs):
			try:
				return _OrigAudioDescription(*args, **kwargs)
			except TypeError:
				# Map legacy kwargs -> new signature
				input_mode = kwargs.pop('input_mode', None)
				input_str = kwargs.pop('input', None)
				sample_rate = kwargs.pop('sample_rate', None) or 48000
				channel_count = kwargs.pop('channel_count', None) or 2
				# bits_per_sample is ignored in new API
				kwargs.pop('bits_per_sample', None)
				media_source = None
				if _MS is not None and hasattr(_MS, 'FFMPEG'):
					media_source = _MS.FFMPEG
				else:
					media_source = getattr(ntgcalls, 'FFMPEG', None)
					if media_source is None and input_mode is not None:
						media_source = input_mode
				return _OrigAudioDescription(media_source, int(sample_rate), int(channel_count), input_str or "")
		setattr(ntgcalls, 'AudioDescription', _compat_AudioDescription)
except Exception:
	pass

# Wrap MediaDescription to accept legacy (audio, video) kwargs
try:
	_OrigMediaDescription = getattr(ntgcalls, 'MediaDescription', None)
	if _OrigMediaDescription is not None:
		def _compat_MediaDescription(*args, **kwargs):
			try:
				return _OrigMediaDescription(*args, **kwargs)
			except TypeError:
				audio = kwargs.pop('audio', None)
				video = kwargs.pop('video', None)
				if 'speaker' not in kwargs and audio is not None:
					kwargs['speaker'] = audio
				if 'camera' not in kwargs and video is not None:
					kwargs['camera'] = video
				return _OrigMediaDescription(*args, **kwargs)
		setattr(ntgcalls, 'MediaDescription', _compat_MediaDescription)
except Exception:
	pass

print("[PATCH] ntgcalls compatibility aliases created successfully")