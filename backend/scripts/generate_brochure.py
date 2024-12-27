import argparse
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def create_brochure(title, hotel, location, content, images, output_path):
    # Create a new image with a white background
    width = 2480  # A4 width at 300 DPI
    height = 3508  # A4 height at 300 DPI
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 120)
        subtitle_font = ImageFont.truetype("arial.ttf", 80)
        content_font = ImageFont.truetype("arial.ttf", 60)
    except:
        # Fallback to default font if arial is not available
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        content_font = ImageFont.load_default()
    
    # Draw title
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) / 2, 100), title, font=title_font, fill='black')
    
    # Draw hotel name and location
    subtitle_text = f"{hotel} - {location}"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((width - subtitle_width) / 2, 300), subtitle_text, font=subtitle_font, fill='black')
    
    # Draw content
    y_position = 500
    wrapped_text = textwrap.fill(content, width=60)
    for line in wrapped_text.split('\n'):
        draw.text((100, y_position), line, font=content_font, fill='black')
        y_position += 80
    
    # Add images
    image_paths = images.split(',')
    image_size = (width // 3 - 100, height // 4)
    x_position = 100
    y_position = height - image_size[1] - 100
    
    for img_path in image_paths[:3]:  # Show up to 3 images
        try:
            with Image.open(img_path) as img:
                img = img.resize(image_size, Image.Resampling.LANCZOS)
                image.paste(img, (x_position, y_position))
                x_position += width // 3
        except Exception as e:
            print(f"Error processing image {img_path}: {e}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the brochure
    image.save(output_path, 'PNG', quality=95)
    print(f"Brochure saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a brochure image')
    parser.add_argument('--title', required=True, help='Brochure title')
    parser.add_argument('--hotel', required=True, help='Hotel name')
    parser.add_argument('--location', required=True, help='Location')
    parser.add_argument('--content', required=True, help='Brochure content')
    parser.add_argument('--images', required=True, help='Comma-separated list of image paths')
    parser.add_argument('--output', required=True, help='Output path for the brochure image')
    
    args = parser.parse_args()
    create_brochure(args.title, args.hotel, args.location, args.content, args.images, args.output)
