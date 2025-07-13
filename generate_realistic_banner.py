#!/usr/bin/env python3
"""
Generate a realistic banner image for Lost Then Found Pet QR Registry
featuring dogs and cats playing in a field with collars and dog tags
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import qrcode
import io
import random
import math

# Banner dimensions
BANNER_WIDTH = 1200
BANNER_HEIGHT = 400

def create_gradient_sky():
    """Create a realistic sky gradient"""
    img = Image.new('RGB', (BANNER_WIDTH, BANNER_HEIGHT), color='white')
    draw = ImageDraw.Draw(img)
    
    # Create sky gradient from light blue to white
    for y in range(BANNER_HEIGHT):
        # Sky gradient: deeper blue at top, lighter toward horizon
        ratio = y / BANNER_HEIGHT
        
        # Sky colors
        sky_blue = (135, 206, 235)  # Sky blue
        horizon_blue = (176, 224, 230)  # Powder blue
        
        r = int(sky_blue[0] + (horizon_blue[0] - sky_blue[0]) * ratio)
        g = int(sky_blue[1] + (horizon_blue[1] - sky_blue[1]) * ratio)
        b = int(sky_blue[2] + (horizon_blue[2] - sky_blue[2]) * ratio)
        
        draw.line([(0, y), (BANNER_WIDTH, y)], fill=(r, g, b))
    
    return img

def add_clouds(img):
    """Add realistic clouds to the sky"""
    draw = ImageDraw.Draw(img)
    
    # Add fluffy clouds
    cloud_color = (255, 255, 255, 180)
    
    # Cloud 1
    cloud_points = [
        (100, 80), (180, 60), (260, 70), (320, 85), (280, 110), (200, 120), (120, 105)
    ]
    draw.polygon(cloud_points, fill=cloud_color)
    
    # Cloud 2
    cloud_points = [
        (800, 50), (900, 40), (980, 55), (1020, 70), (970, 90), (880, 95), (820, 80)
    ]
    draw.polygon(cloud_points, fill=cloud_color)
    
    # Cloud 3 (smaller)
    cloud_points = [
        (500, 90), (560, 85), (600, 95), (580, 110), (520, 105)
    ]
    draw.polygon(cloud_points, fill=cloud_color)
    
    return img

def create_grass_field(img):
    """Create a realistic grass field"""
    draw = ImageDraw.Draw(img)
    
    # Ground level starts at about 60% down
    ground_level = int(BANNER_HEIGHT * 0.6)
    
    # Create grass gradient
    for y in range(ground_level, BANNER_HEIGHT):
        ratio = (y - ground_level) / (BANNER_HEIGHT - ground_level)
        
        # Grass colors - darker green at bottom, lighter at top
        light_green = (124, 252, 0)  # Lawn green
        dark_green = (34, 139, 34)   # Forest green
        
        r = int(light_green[0] + (dark_green[0] - light_green[0]) * ratio)
        g = int(light_green[1] + (dark_green[1] - light_green[1]) * ratio)
        b = int(light_green[2] + (dark_green[2] - light_green[2]) * ratio)
        
        draw.line([(0, y), (BANNER_WIDTH, y)], fill=(r, g, b))
    
    # Add some grass texture
    for i in range(200):
        x = random.randint(0, BANNER_WIDTH)
        y = random.randint(ground_level, BANNER_HEIGHT - 5)
        length = random.randint(3, 8)
        
        # Grass blade color variation
        grass_colors = [(60, 179, 113), (50, 205, 50), (34, 139, 34), (46, 125, 50)]
        color = random.choice(grass_colors)
        
        draw.line([(x, y), (x + random.randint(-2, 2), y - length)], fill=color, width=1)
    
    return img

def draw_realistic_dog(draw, x, y, size=80):
    """Draw a realistic dog silhouette"""
    # Dog body (oval)
    body_width = size
    body_height = size * 0.6
    draw.ellipse([x, y, x + body_width, y + body_height], fill=(139, 69, 19))  # Saddle brown
    
    # Head (circle)
    head_size = size * 0.4
    head_x = x + body_width * 0.8
    head_y = y - head_size * 0.3
    draw.ellipse([head_x, head_y, head_x + head_size, head_y + head_size], fill=(160, 82, 45))
    
    # Ears
    ear_width = head_size * 0.3
    ear_height = head_size * 0.4
    # Left ear
    draw.ellipse([head_x - ear_width*0.2, head_y + head_size*0.1, 
                  head_x + ear_width*0.8, head_y + head_size*0.1 + ear_height], fill=(101, 67, 33))
    # Right ear
    draw.ellipse([head_x + head_size*0.4, head_y + head_size*0.1,
                  head_x + head_size*0.4 + ear_width, head_y + head_size*0.1 + ear_height], fill=(101, 67, 33))
    
    # Legs
    leg_width = size * 0.1
    leg_height = size * 0.4
    for i, leg_x in enumerate([x + size*0.1, x + size*0.3, x + size*0.6, x + size*0.8]):
        draw.rectangle([leg_x, y + body_height, leg_x + leg_width, y + body_height + leg_height], 
                      fill=(139, 69, 19))
    
    # Tail
    tail_start_x = x - size * 0.1
    tail_start_y = y + body_height * 0.3
    tail_end_x = x - size * 0.3
    tail_end_y = y + body_height * 0.1
    draw.line([(tail_start_x, tail_start_y), (tail_end_x, tail_end_y)], fill=(139, 69, 19), width=8)
    
    return head_x + head_size/2, head_y + head_size/2  # Return collar position

def draw_realistic_cat(draw, x, y, size=60):
    """Draw a realistic cat silhouette"""
    # Cat body (oval, smaller than dog)
    body_width = size
    body_height = size * 0.5
    draw.ellipse([x, y, x + body_width, y + body_height], fill=(105, 105, 105))  # Dim gray
    
    # Head (circle)
    head_size = size * 0.35
    head_x = x + body_width * 0.8
    head_y = y - head_size * 0.2
    draw.ellipse([head_x, head_y, head_x + head_size, head_y + head_size], fill=(128, 128, 128))
    
    # Pointed ears (triangles)
    ear_size = head_size * 0.3
    # Left ear
    ear_points = [
        (head_x + head_size*0.2, head_y + head_size*0.1),
        (head_x + head_size*0.1, head_y - ear_size*0.5),
        (head_x + head_size*0.4, head_y)
    ]
    draw.polygon(ear_points, fill=(105, 105, 105))
    
    # Right ear
    ear_points = [
        (head_x + head_size*0.6, head_y),
        (head_x + head_size*0.9, head_y - ear_size*0.5),
        (head_x + head_size*0.8, head_y + head_size*0.1)
    ]
    draw.polygon(ear_points, fill=(105, 105, 105))
    
    # Legs (thinner than dog)
    leg_width = size * 0.08
    leg_height = size * 0.3
    for i, leg_x in enumerate([x + size*0.15, x + size*0.35, x + size*0.65, x + size*0.85]):
        draw.rectangle([leg_x, y + body_height, leg_x + leg_width, y + body_height + leg_height], 
                      fill=(105, 105, 105))
    
    # Tail (curved)
    tail_start_x = x - size * 0.05
    tail_start_y = y + body_height * 0.2
    # Draw curved tail with multiple segments
    for i in range(5):
        segment_x = tail_start_x - i * size * 0.1
        segment_y = tail_start_y - i * size * 0.05 + math.sin(i) * size * 0.1
        next_x = tail_start_x - (i+1) * size * 0.1
        next_y = tail_start_y - (i+1) * size * 0.05 + math.sin(i+1) * size * 0.1
        draw.line([(segment_x, segment_y), (next_x, next_y)], fill=(105, 105, 105), width=6)
    
    return head_x + head_size/2, head_y + head_size/2  # Return collar position

def draw_collar_with_tag(draw, x, y, has_qr=True):
    """Draw a collar with a dog tag"""
    # Collar
    collar_width = 40
    collar_height = 8
    collar_x = x - collar_width // 2
    collar_y = y
    
    draw.rectangle([collar_x, collar_y, collar_x + collar_width, collar_y + collar_height], 
                  fill=(139, 0, 0), outline=(0, 0, 0), width=1)  # Dark red collar
    
    # Dog tag
    tag_width = 16
    tag_height = 20
    tag_x = x - tag_width // 2
    tag_y = collar_y + collar_height
    
    # Tag background
    draw.rectangle([tag_x, tag_y, tag_x + tag_width, tag_y + tag_height], 
                  fill=(192, 192, 192), outline=(0, 0, 0), width=1)  # Silver tag
    
    return tag_x, tag_y, tag_width, tag_height

def create_mini_qr_code(data, size=12):
    """Create a tiny QR code for the dog tag"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=0,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((size, size), Image.Resampling.NEAREST)
    return qr_img

def create_mini_logo(size=12):
    """Create a tiny logo for the dog tag"""
    logo_img = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(logo_img)
    
    # Simple logo: circle with "LTF" text
    draw.ellipse([1, 1, size-1, size-1], fill=(0, 100, 200), outline=(0, 0, 0))
    
    # Try to add tiny text (might be too small to read but adds detail)
    try:
        font = ImageFont.load_default()
        draw.text((size//4, size//4), "LTF", fill="white", font=font)
    except:
        # If text is too small, just draw a small white dot
        draw.ellipse([size//3, size//3, 2*size//3, 2*size//3], fill="white")
    
    return logo_img

def add_title_text(img):
    """Add the site title to the banner"""
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a better font if available
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Main title
    title = "Lost Then Found"
    subtitle = "Pet QR Registry"
    
    # Calculate text positioning (center-left area)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
    
    # Position text in upper left area
    title_x = 50
    title_y = 60
    subtitle_x = 50
    subtitle_y = title_y + title_height + 10
    
    # Add text shadow for better readability
    shadow_offset = 2
    draw.text((title_x + shadow_offset, title_y + shadow_offset), title, 
              fill=(0, 0, 0, 128), font=title_font)
    draw.text((subtitle_x + shadow_offset, subtitle_y + shadow_offset), subtitle, 
              fill=(0, 0, 0, 128), font=subtitle_font)
    
    # Main text
    draw.text((title_x, title_y), title, fill=(255, 255, 255), font=title_font)
    draw.text((subtitle_x, subtitle_y), subtitle, fill=(255, 255, 255), font=subtitle_font)

def main():
    """Generate the realistic banner image"""
    print("Creating realistic banner for Lost Then Found Pet QR Registry...")
    
    # Create base image with sky
    img = create_gradient_sky()
    
    # Add clouds
    img = add_clouds(img)
    
    # Add grass field
    img = create_grass_field(img)
    
    # Get drawing context
    draw = ImageDraw.Draw(img)
    
    # Add pets with collars and tags
    pets = [
        # (type, x, y, size, has_qr)
        ('dog', 300, 250, 80, True),
        ('cat', 450, 280, 60, False),
        ('dog', 600, 240, 90, False),
        ('cat', 750, 285, 55, True),
        ('dog', 900, 260, 85, True),
        ('cat', 1050, 275, 65, False),
    ]
    
    for pet_type, x, y, size, has_qr in pets:
        if pet_type == 'dog':
            collar_x, collar_y = draw_realistic_dog(draw, x, y, size)
        else:
            collar_x, collar_y = draw_realistic_cat(draw, x, y, size)
        
        # Draw collar and get tag position
        tag_x, tag_y, tag_width, tag_height = draw_collar_with_tag(draw, collar_x, collar_y, has_qr)
        
        # Add QR code or logo to tag
        if has_qr:
            # Create mini QR code
            qr_img = create_mini_qr_code(f"https://ltfpqrr.com/pet/{random.randint(1000, 9999)}", 
                                       size=int(tag_width-2))
            img.paste(qr_img, (int(tag_x+1), int(tag_y+1)))
        else:
            # Create mini logo
            logo_img = create_mini_logo(size=int(tag_width-2))
            img.paste(logo_img, (int(tag_x+1), int(tag_y+1)))
    
    # Add title text
    add_title_text(img)
    
    # Apply slight blur to background for depth
    background = img.crop((0, 0, BANNER_WIDTH, int(BANNER_HEIGHT * 0.3)))
    background = background.filter(ImageFilter.GaussianBlur(radius=0.5))
    img.paste(background, (0, 0))
    
    # Save the image
    output_path = '/Users/justinkumpe/Documents/LTFPQRR/static/assets/realistic_banner.png'
    img.save(output_path, 'PNG', quality=95)
    print(f"Realistic banner saved to: {output_path}")
    
    # Also save a backup version
    backup_path = '/Users/justinkumpe/Documents/LTFPQRR/static/assets/banner_backup.png'
    img.save(backup_path, 'PNG', quality=95)
    print(f"Backup saved to: {backup_path}")

if __name__ == "__main__":
    main()
