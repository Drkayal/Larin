"""
Compatibility patch for py-tgcalls 1.0.9 with ntgcalls 2.x
This patch creates aliases for StreamStatus attributes to maintain compatibility
"""

import ntgcalls

# Create aliases for compatibility with py-tgcalls 1.0.9
if not hasattr(ntgcalls.StreamStatus, 'Playing'):
    if hasattr(ntgcalls.StreamStatus, 'ACTIVE'):
        ntgcalls.StreamStatus.Playing = ntgcalls.StreamStatus.ACTIVE

if not hasattr(ntgcalls.StreamStatus, 'Paused'):
    if hasattr(ntgcalls.StreamStatus, 'PAUSED'):
        ntgcalls.StreamStatus.Paused = ntgcalls.StreamStatus.PAUSED

if not hasattr(ntgcalls.StreamStatus, 'Idling'):
    if hasattr(ntgcalls.StreamStatus, 'IDLING'):
        ntgcalls.StreamStatus.Idling = ntgcalls.StreamStatus.IDLING

print("[PATCH] ntgcalls compatibility aliases created successfully")