import os
import math
import zlib
import struct

def draw_shield_png(size, filepath):
    width = size
    height = size
    
    # Background color: Dark Navy #0f172a (15, 23, 42)
    bg_r, bg_g, bg_b = 15, 23, 42
    
    # Shield Outer fill: Cyan/Blue #0284c7 (2, 132, 199)
    s_r, s_g, s_b = 2, 132, 199
    
    # Shield Inner Accent: Sky Blue #38bdf8 (56, 189, 248)
    i_r, i_g, i_b = 56, 189, 248
    
    # Emblem/Lock fill: White #ffffff (255, 255, 255)
    w_r, w_g, w_b = 255, 255, 255
    
    cx = width / 2.0
    top_y = height * 0.18
    bottom_y = height * 0.84
    shield_w = width * 0.38
    shield_h = bottom_y - top_y
    
    raw_pixels = []
    
    for y in range(height):
        row = bytearray([0]) # PNG filter type 0 (None)
        for x in range(width):
            # Normalize coordinates relative to center
            dx = abs(x - cx)
            dy = y - top_y
            
            is_shield = False
            is_inner_shield = False
            is_emblem = False
            
            if top_y <= y <= bottom_y:
                # Shield parametric contour
                # Top half (y from 0 to 0.45 * shield_h): wide box shape with slight curve
                # Bottom half (y from 0.45 to 1.0 * shield_h): tapers down to bottom_y
                t = (y - top_y) / shield_h
                
                if t < 0.4:
                    # Slightly outward expanding top
                    allowed_w = shield_w * (1.0 - 0.05 * math.sin(t * math.pi / 0.4))
                else:
                    # Taper down smoothly to 0 at t=1.0
                    factor = 1.0 - math.pow((t - 0.4) / 0.6, 1.6)
                    allowed_w = shield_w * max(0.0, factor)
                
                if dx <= allowed_w:
                    is_shield = True
                    
                    # Inner shield border
                    if dx <= allowed_w * 0.85 and (0.05 <= t <= 0.92):
                        is_inner_shield = True
                        
                        # Central Lock/Keyhole Emblem inside shield
                        lock_cx = cx
                        lock_cy = top_y + shield_h * 0.45
                        lock_r = shield_w * 0.28
                        
                        # Circle top of lock + shackle
                        dist_lock = math.sqrt((x - lock_cx)**2 + (y - (lock_cy - lock_r*0.3))**2)
                        if dist_lock <= lock_r * 0.5:
                            is_emblem = True
                        
                        # Body of lock
                        if abs(x - lock_cx) <= lock_r * 0.55 and (lock_cy - lock_r*0.2 <= y <= lock_cy + lock_r*0.6):
                            is_emblem = True
                            
                        # Keyhole cutout inside emblem
                        if is_emblem:
                            kh_dist = math.sqrt((x - lock_cx)**2 + (y - (lock_cy + lock_r*0.1))**2)
                            if kh_dist <= lock_r * 0.18:
                                is_emblem = False
                            if abs(x - lock_cx) <= lock_r * 0.08 and (lock_cy + lock_r*0.1 <= y <= lock_cy + lock_r*0.38):
                                is_emblem = False
            
            # Determine color
            if is_emblem:
                r, g, b = w_r, w_g, w_b
            elif is_inner_shield:
                r, g, b = i_r, i_g, i_b
            elif is_shield:
                r, g, b = s_r, s_g, s_b
            else:
                r, g, b = bg_r, bg_g, bg_b
                
            row.extend([r, g, b])
        raw_pixels.append(bytes(row))
        
    raw_data = b''.join(raw_pixels)
    
    # Build PNG
    header = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)
    
    idat_data = zlib.compress(raw_data, level=9)
    idat = struct.pack('>I', len(idat_data)) + b'IDAT' + idat_data + struct.pack('>I', zlib.crc32(b'IDAT' + idat_data) & 0xffffffff)
    
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)
    
    with open(filepath, 'wb') as f:
        f.write(header + ihdr + idat + iend)

os.makedirs('static/icons', exist_ok=True)
draw_shield_png(192, 'static/icons/icon-192.png')
draw_shield_png(512, 'static/icons/icon-512.png')
print("Shield icons generated for 192x192 and 512x512!")
