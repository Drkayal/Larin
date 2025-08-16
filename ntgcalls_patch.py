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

print("[PATCH] ntgcalls compatibility aliases created successfully")