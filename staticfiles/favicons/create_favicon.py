import struct

def create_favicon():
    """Create a simple 16x16 favicon.ico file"""
    # ICO header (6 bytes)
    ico_header = struct.pack('<HHH', 0, 1, 1)  # Reserved, Type (1=ICO), Count
    
    # Image directory entry (16 bytes)
    width = 16
    height = 16
    colors = 0  # 0 = 256+ colors
    reserved = 0
    planes = 1
    bit_count = 32
    image_size = 40 + (width * height * 4)  # DIB header + RGBA data
    image_offset = 6 + 16  # After ICO header + directory entry
    
    dir_entry = struct.pack('<BBBBHHLL', width, height, colors, reserved, planes, bit_count, image_size, image_offset)
    
    # DIB header (40 bytes)
    dib_header = struct.pack('<LLLHHLLLLLL', 
        40,  # header size
        width,  # width
        height * 2,  # height * 2 for ICO
        1,  # planes
        32,  # bits per pixel
        0,  # compression
        width * height * 4,  # image size
        0, 0, 0, 0  # other fields
    )
    
    # Create pixel data (16x16 RGBA)
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            # Create a simple SMS-like icon pattern
            if (x >= 2 and x <= 13 and y >= 4 and y <= 11):
                if (x == 2 or x == 13 or y == 4 or y == 11):
                    # Border - blue
                    pixels.extend([234, 110, 102, 255])  # BGRA format
                else:
                    # Inside - white
                    pixels.extend([255, 255, 255, 255])
            elif (x >= 6 and x <= 10 and y >= 7 and y <= 8):
                # Text lines - dark blue
                pixels.extend([162, 75, 118, 255])
            else:
                # Transparent background
                pixels.extend([0, 0, 0, 0])
    
    # Write the ICO file
    with open('favicon.ico', 'wb') as f:
        f.write(ico_header)
        f.write(dir_entry)
        f.write(dib_header)
        f.write(pixels)
    
    print('Created favicon.ico successfully!')

def create_png_icons():
    """Create PNG icons in various sizes"""
    try:
        from PIL import Image, ImageDraw
        
        # Create images in different sizes
        sizes = [16, 32, 48, 64, 128, 180, 192, 512]
        
        for size in sizes:
            # Create a new image with transparent background
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Calculate proportional sizes
            border_width = max(1, size // 16)
            margin = size // 8
            
            # Draw SMS bubble
            bubble_rect = [margin, margin, size - margin, size - margin // 2]
            draw.rounded_rectangle(bubble_rect, radius=size//16, fill=(102, 110, 234, 255), outline=(102, 110, 234, 255))
            
            # Draw inner area
            inner_rect = [margin + border_width, margin + border_width, 
                         size - margin - border_width, size - margin // 2 - border_width]
            draw.rounded_rectangle(inner_rect, radius=size//20, fill=(255, 255, 255, 255))
            
            # Draw text lines
            line_height = max(1, size // 32)
            line_margin = size // 4
            y_center = margin + (size - margin) // 4
            
            for i in range(3):
                y_pos = y_center + i * line_height * 2
                if y_pos < size - margin // 2 - line_height:
                    draw.rectangle([line_margin, y_pos, size - line_margin, y_pos + line_height], 
                                 fill=(118, 75, 162, 255))
            
            # Save the image
            img.save(f'favicon-{size}x{size}.png', 'PNG')
            print(f'Created favicon-{size}x{size}.png')
    
    except ImportError:
        print("PIL not available for PNG creation. ICO file created successfully.")
        print("You can use online tools to create PNG versions from the ICO file.")

if __name__ == "__main__":
    create_favicon()
    create_png_icons()
