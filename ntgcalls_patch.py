"""
Compatibility patch for py-tgcalls 1.0.9 with ntgcalls 1.2.3
This patch creates aliases for StreamStatus attributes to maintain compatibility
"""

import ntgcalls

# Create aliases for compatibility with py-tgcalls 1.0.9
if not hasattr(ntgcalls.StreamStatus, 'Playing'):
    ntgcalls.StreamStatus.Playing = ntgcalls.StreamStatus.PLAYING

if not hasattr(ntgcalls.StreamStatus, 'Paused'):
    ntgcalls.StreamStatus.Paused = ntgcalls.StreamStatus.PAUSED

if not hasattr(ntgcalls.StreamStatus, 'Idling'):
    ntgcalls.StreamStatus.Idling = ntgcalls.StreamStatus.IDLING

print("[PATCH] ntgcalls compatibility aliases created successfully")