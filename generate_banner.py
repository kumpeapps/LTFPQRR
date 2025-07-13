#!/usr/bin/env python3
"""
Generate a custom banner image for LTFPQRR featuring dogs and cats playing in a field
with collars and dog tags showing QR codes and logos.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import qrcode
import random
import math
import os

def create_qr_code(data, size=50):
    """Create a small QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=2,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
    return qr_img

def create_simple_logo(size=50):
    """Create a simple LTFPQRR logo for tags"""
    logo = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(logo)
    
    # Draw a simple paw print
    pad_size = size // 3
    toe_size = size // 8
    
    # Main pad
    draw.ellipse([size//2 - pad_size//2, size//2 - pad_size//4, 
                  size//2 + pad_size//2, size//2 + pad_size//2], 
                 fill=(65, 105, 225, 255))
    
    # Toes
    positions = [
        (size//2 - pad_size//3, size//2 - pad_size//2),
        (size//2, size//2 - pad_size//1.5),
        (size//2 + pad_size//3, size//2 - pad_size//2),
    ]
    
    for x, y in positions:
        draw.ellipse([x - toe_size//2, y - toe_size//2, 
                      x + toe_size//2, y + toe_size//2], 
                     fill=(65, 105, 225, 255))
    
    return logo

def draw_animal(draw, x, y, animal_type, size=60):
    """Draw a simple cartoon animal (dog or cat)"""
    colors = {
        'dog': [(139, 69, 19), (160, 82, 45)],  # Brown shades
        'cat': [(105, 105, 105), (128, 128, 128)]  # Gray shades
    }
    
    color1, color2 = colors[animal_type]
    
    # Body (oval)
    body_width = size
    body_height = size // 2
    draw.ellipse([x - body_width//2, y - body_height//2, 
                  x + body_width//2, y + body_height//2], 
                 fill=color1, outline=(0, 0, 0, 255), width=2)
    
    # Head (circle)
    head_size = size // 2
    head_y = y - body_height//2 - head_size//2
    draw.ellipse([x - head_size//2, head_y - head_size//2, 
                  x + head_size//2, head_y + head_size//2], 
                 fill=color2, outline=(0, 0, 0, 255), width=2)
    
    # Ears
    ear_size = head_size // 3
    if animal_type == 'dog':
        # Floppy dog ears
        draw.ellipse([x - head_size//2 - ear_size//2, head_y - head_size//4, 
                      x - head_size//2 + ear_size//2, head_y + ear_size], 
                     fill=color1, outline=(0, 0, 0, 255), width=1)
        draw.ellipse([x + head_size//2 - ear_size//2, head_y - head_size//4, 
                      x + head_size//2 + ear_size//2, head_y + ear_size], 
                     fill=color1, outline=(0, 0, 0, 255), width=1)
    else:
        # Pointed cat ears
        points1 = [(x - head_size//3, head_y - head_size//2), 
                   (x - head_size//2, head_y - head_size//3), 
                   (x - head_size//6, head_y - head_size//3)]
        points2 = [(x + head_size//3, head_y - head_size//2), 
                   (x + head_size//2, head_y - head_size//3), 
                   (x + head_size//6, head_y - head_size//3)]
        draw.polygon(points1, fill=color1, outline=(0, 0, 0, 255))
        draw.polygon(points2, fill=color1, outline=(0, 0, 0, 255))
    
    # Eyes
    eye_size = 4
    draw.ellipse([x - head_size//4 - eye_size//2, head_y - head_size//6, 
                  x - head_size//4 + eye_size//2, head_y - head_size//6 + eye_size], 
                 fill=(0, 0, 0, 255))
    draw.ellipse([x + head_size//4 - eye_size//2, head_y - head_size//6, 
                  x + head_size//4 + eye_size//2, head_y - head_size//6 + eye_size], 
                 fill=(0, 0, 0, 255))
    
    # Nose
    nose_size = 3
    draw.ellipse([x - nose_size//2, head_y, x + nose_size//2, head_y + nose_size], 
                 fill=(0, 0, 0, 255))
    
    # Collar
    collar_y = head_y + head_size//2 - 5
    draw.rectangle([x - head_size//2, collar_y, x + head_size//2, collar_y + 8], 
                   fill=(255, 0, 0, 255), outline=(139, 0, 0, 255), width=1)
    
    return collar_y + 4  # Return collar center for tag placement

def draw_tag(img, x, y, tag_content, tag_type='qr'):
    """Draw a dog tag with either QR code or logo"""
    tag_size = 30
    
    # Create tag background (circular)
    tag_img = Image.new('RGBA', (tag_size, tag_size), (0, 0, 0, 0))
    tag_draw = ImageDraw.Draw(tag_img)
    tag_draw.ellipse([0, 0, tag_size-1, tag_size-1], 
                     fill=(192, 192, 192, 255), outline=(128, 128, 128, 255), width=2)
    
    # Add content to tag
    if tag_type == 'qr':
        qr_code = create_qr_code(tag_content, size=tag_size-8)
        qr_code = qr_code.convert('RGBA')
        tag_img.paste(qr_code, (4, 4), qr_code)
    else:
        logo = create_simple_logo(size=tag_size-8)
        tag_img.paste(logo, (4, 4), logo)
    
    # Paste tag onto main image
    img.paste(tag_img, (x - tag_size//2, y - tag_size//2), tag_img)

def create_banner():
    """Create the main banner image"""
    width, height = 1200, 400
    
    # Create base image with sky gradient
    img = Image.new('RGB', (width, height), (135, 206, 235))  # Sky blue
    draw = ImageDraw.Draw(img)
    
    # Draw sky gradient
    for y in range(height):
        ratio = y / height
        r = int(135 + (255 - 135) * ratio * 0.3)
        g = int(206 + (255 - 206) * ratio * 0.3)
        b = int(235 + (255 - 235) * ratio * 0.1)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Draw grass field
    grass_height = height // 3
    for y in range(height - grass_height, height):
        ratio = (y - (height - grass_height)) / grass_height
        r = int(34 + (50 - 34) * ratio)
        g = int(139 + (205 - 139) * ratio)
        b = int(34 + (50 - 34) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add some clouds
    cloud_positions = [(200, 80), (600, 60), (1000, 90)]
    for cx, cy in cloud_positions:
        for i in range(5):
            offset_x = random.randint(-20, 20)
            offset_y = random.randint(-10, 10)
            size = random.randint(30, 50)
            draw.ellipse([cx + offset_x - size//2, cy + offset_y - size//2,
                         cx + offset_x + size//2, cy + offset_y + size//2],
                        fill=(255, 255, 255, 200))
    
    # Draw animals with collars and tags
    animals = [
        ('dog', 200, height - 120),
        ('cat', 350, height - 100),
        ('dog', 500, height - 140),
        ('cat', 650, height - 110),
        ('dog', 800, height - 130),
        ('cat', 950, height - 105),
    ]
    
    tag_data = [
        ('qr', 'https://ltfpqrr.com/pet/1'),
        ('logo', ''),
        ('qr', 'https://ltfpqrr.com/pet/2'),
        ('logo', ''),
        ('qr', 'https://ltfpqrr.com/pet/3'),
        ('logo', ''),
    ]
    
    for i, (animal_type, x, y) in enumerate(animals):
        collar_y = draw_animal(draw, x, y, animal_type)
        tag_type, tag_content = tag_data[i]
        # Offset tag slightly from collar center
        tag_x = x + random.randint(-15, 15)
        tag_y = collar_y + random.randint(10, 20)
        draw_tag(img, tag_x, tag_y, tag_content, tag_type)
    
    # Add title text
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Add semi-transparent overlay for text
    overlay = Image.new('RGBA', (width, 120), (255, 255, 255, 180))
    img.paste(overlay, (0, 20), overlay)
    
    # Draw title
    title = "Lost Things Found: Pet Quick Response Registry"
    subtitle = "Reuniting Pets with Their Families Through Technology"
    
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) // 2, 30), title, 
              fill=(65, 105, 225), font=title_font)
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((width - subtitle_width) // 2, 85), subtitle, 
              fill=(25, 25, 112), font=subtitle_font)
    
    return img

def main():
    print("Generating LTFPQRR banner with dogs, cats, and QR code tags...")
    
    # Create the banner
    banner = create_banner()
    
    # Save the banner
    banner_path = "static/assets/banner_pets_qr.png"
    os.makedirs(os.path.dirname(banner_path), exist_ok=True)
    banner.save(banner_path, "PNG", quality=95)
    
    print(f"Banner saved to: {banner_path}")
    print("Banner features:")
    print("- 6 animals (3 dogs, 3 cats) playing in a grassy field")
    print("- Each animal has a collar with a dog tag")
    print("- 3 tags show QR codes linking to pet info pages")
    print("- 3 tags show the LTFPQRR paw print logo")
    print("- Sky background with clouds")
    print("- Professional title overlay")

if __name__ == "__main__":
    main()
