from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import os
import random
from models.test_image_generation import test_image_generation
import math
import requests
import time
from collections import deque
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io

# Rate limiting setup
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
MAX_REQUESTS_PER_WINDOW = 100
request_timestamps = deque()

class SinglePageBrochureGenerator:
    def __init__(self, hotel_name, location, layout='full_bleed'):
        """Initialize the brochure generator with hotel name and location"""
        # Remove any extra 'The' from the hotel name
        if hotel_name.startswith("'The ") or hotel_name.startswith('"The '):
            hotel_name = hotel_name[5:]  # Remove the extra 'The ' but don't add quote
        elif hotel_name.lower().startswith("the "):
            hotel_name = hotel_name[4:]  # Remove 'The ' from the beginning
        self.hotel_name = hotel_name.strip()
        self.location = location
        self.layout = 'full_bleed'  # Always use full_bleed layout
        self.width = 1780
        self.height = 2480
        
        # Initialize descriptions dictionary
        self.descriptions = {}
        
        # Load fonts with adjusted sizes
        try:
            self.font_title = ImageFont.truetype("fonts/Montserrat-Bold.ttf", 140)
            self.font_heading = ImageFont.truetype("fonts/Montserrat-Bold.ttf", 90)
            self.font_text = ImageFont.truetype("fonts/Montserrat-Regular.ttf", 54)
            self.font_small = ImageFont.truetype("fonts/Montserrat-Regular.ttf", 72)  # Increased to 72px
        except Exception as e:
            print("Using system fonts as fallback...")
            self.font_title = ImageFont.truetype("arial.ttf", 140)
            self.font_heading = ImageFont.truetype("arial.ttf", 90)
            self.font_text = ImageFont.truetype("arial.ttf", 54)
            self.font_small = ImageFont.truetype("arial.ttf", 72)  # Increased to 72px
        
        # Define colors
        self.colors = {
            'primary': (20, 20, 20),  # Almost black
            'secondary': (255, 255, 255),  # White
            'accent': (200, 170, 110),  # Gold
        }
        
        # Define system fonts
        self.system_fonts = {
            'title': 'arial.ttf',
            'subtitle': 'arial.ttf',
            'heading': 'arial.ttf',
            'text': 'arial.ttf',
            'decorative': 'arial.ttf',
            'small': 'arial.ttf'
        }
        
        # Initialize fonts with dynamic sizing
        print("Using system fonts as fallback...")
        self.font_title = ImageFont.truetype(self.system_fonts['title'], 140)  # Will be resized dynamically
        self.font_subtitle = ImageFont.truetype(self.system_fonts['subtitle'], 48)
        self.font_heading = ImageFont.truetype(self.system_fonts['heading'], 64)
        self.font_text = ImageFont.truetype(self.system_fonts['text'], 36)
        self.font_decorative = ImageFont.truetype(self.system_fonts['decorative'], 32)
        self.font_small = ImageFont.truetype(self.system_fonts['small'], 24)
        
        # Create directories if they don't exist
        for directory in ['generated_images', 'generated_brochures']:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {str(e)}")
                # Continue execution even if directory creation fails
                pass
        
        # Define image paths with consistent separators and space handling
        safe_hotel_name = self.hotel_name.replace(' ', '_')
        self.exterior_image_path = f'generated_images/{safe_hotel_name}_exterior.png'
        self.room_image_path = f'generated_images/{safe_hotel_name}_room.png'
        self.restaurant_image_path = f'generated_images/{safe_hotel_name}_restaurant.png'
        
        # Generate descriptions using T5 model
        self.generate_descriptions()
        
        # Pricing information
        self.pricing = {
            'Deluxe Room': '$550/night',
            'Ocean Suite': '$850/night',
            'Presidential Villa': '$2,500/night'
        }
        
        # Valid layouts
        self.valid_layouts = [
            'default',
            'modern',
            'classic',
            'full_bleed'
        ]
        
    def generate_descriptions(self):
        """Generate descriptions using T5 model"""
        print("\nGenerating descriptions from T5...")
        
        # Prepare prompts for T5 that incorporate hotel name and location
        prompts = {
            "overview": f"Generate a brief description of {self.hotel_name} in {self.location}, highlighting its main features and surroundings",
            "room": f"Describe the luxury accommodations at {self.hotel_name} in {self.location}, focusing on room features and views",
            "dining": f"Describe the dining experience at {self.hotel_name} in {self.location}. Focus on: 1) Local cuisine specialties from {self.location}, 2) Signature dishes, 3) Restaurant atmosphere and views. Make it specific to the location's culinary culture.",
            "amenities": f"List 6 ultra-luxury amenities for {self.hotel_name} in {self.location}, focusing on unique features that match the location. Format as simple list."
        }

        # Define default location-based dining descriptions
        location_based_dining = {
            'beach': f"Experience world-class dining with fresh seafood and tropical flavors at our oceanfront restaurant. Our expert chefs combine local {self.location} specialties with international cuisine, served in a stunning setting with panoramic ocean views.",
            'mountain': f"Savor exceptional cuisine at our signature mountain-view restaurant, where local {self.location} ingredients meet innovative cooking techniques. Enjoy regional specialties and international dishes while taking in breathtaking alpine vistas.",
            'city': f"Indulge in refined dining at our acclaimed restaurant, featuring a sophisticated blend of {self.location} culinary traditions and contemporary gastronomy. Our master chefs create memorable dining experiences in an elegant urban setting.",
            'resort': f"Discover culinary excellence at our signature restaurant, where {self.location}'s finest ingredients are transformed into extraordinary dishes. Enjoy a perfect blend of local specialties and international cuisine in an atmosphere of refined luxury."
        }

        # Determine location type for fallback
        location_lower = f"{self.location} {self.hotel_name}".lower()
        if any(word in location_lower for word in ['beach', 'coast', 'sea', 'ocean', 'bay', 'island']):
            location_type = 'beach'
        elif any(word in location_lower for word in ['mountain', 'hill', 'alps', 'peak', 'cliff']):
            location_type = 'mountain'
        elif any(word in location_lower for word in ['city', 'town', 'urban', 'metro']):
            location_type = 'city'
        else:
            location_type = 'resort'

        # Try to get descriptions from T5
        try:
            for key, prompt in prompts.items():
                response = requests.post(
                    "http://127.0.0.1:8005/generate",
                    json={"prompt": prompt, "max_length": 150}
                )
                if response.status_code == 200:
                    generated_text = response.json()["generated_text"].strip()
                    if key == "dining":
                        # Validate dining description
                        if len(generated_text) > 50 and self.location.lower() in generated_text.lower():
                            self.descriptions[key] = generated_text
                        else:
                            self.descriptions[key] = location_based_dining[location_type]
                    elif key == "amenities":
                        # Parse amenities into a list
                        amenities_text = generated_text.split("\n")
                        t5_amenities = []
                        for amenity in amenities_text:
                            clean_amenity = amenity.strip()
                            clean_amenity = ' '.join(clean_amenity.split()[1:]) if clean_amenity and (clean_amenity[0].isdigit() or clean_amenity[0] in '.-') else clean_amenity
                            if clean_amenity and len(t5_amenities) < 6:
                                t5_amenities.append(clean_amenity)
                        
                        if len(t5_amenities) == 6:
                            self.amenities = t5_amenities
                    else:
                        self.descriptions[key] = generated_text
                else:
                    print(f"Error generating {key} description: {response.status_code}")
                    if key == "dining":
                        self.descriptions[key] = location_based_dining[location_type]
                    else:
                        self.descriptions[key] = ""
                    
            # Generate appropriate email domain based on hotel name
            hotel_domain = self.hotel_name.lower()
            hotel_domain = hotel_domain.replace("'", "").replace('"', "")
            if hotel_domain.startswith("the "):
                hotel_domain = hotel_domain[4:]  # Remove 'the ' from the beginning
            hotel_domain = hotel_domain.replace(" ", "")
            self.contact_email = f"reservations@{hotel_domain}.com"
            
            # Generate custom prompts for image generation based on location
            self.custom_prompts = {
                "exterior": f"Professional architectural photography of {self.hotel_name} in {self.location}, luxury resort architecture, stunning surroundings, high-end resort photography, 4k, detailed, professional lighting",
                "room": f"Interior photography of a luxury suite at {self.hotel_name}, {self.location}, modern design, premium furnishings, panoramic views, professional hotel photography, 4k, detailed",
                "restaurant": f"Fine dining restaurant interior at {self.hotel_name}, {self.location}, elegant modern decor, ambient lighting, professional restaurant photography, 4k, detailed"
            }
            
        except Exception as e:
            print(f"Error in description generation: {str(e)}")
            self.get_fallback_description("all")
            
    def get_descriptions_from_t5(self):
        try:
            # Define prompts for different sections
            prompts = {
                'overview': f"Generate a luxurious description for {self.hotel_name} in {self.location}. Focus on the exclusive location, stunning views, and world-class service.",
                'rooms': f"Describe the luxurious rooms at {self.hotel_name}. Highlight the elegant design, premium amenities, and breathtaking views.",
                'restaurant': f"Describe the fine dining experience at {self.hotel_name}. Focus on the culinary excellence, ambiance, and scenic views."
            }
            
            descriptions = {}
            max_retries = 3
            
            for section, prompt in prompts.items():
                for attempt in range(max_retries):
                    try:
                        response = requests.post(
                            'http://127.0.0.1:8005/generate',
                            json={
                                'prompt': prompt,
                                'max_length': 100,
                                'temperature': 0.7
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            descriptions[section] = response.json()['generated_text']
                            break
                        elif response.status_code == 429:  # Rate limit
                            if attempt < max_retries - 1:
                                time.sleep(3)  # Wait before retry
                                continue
                            else:
                                print(f"Error generating description: {response.status_code}")
                                descriptions[section] = self.get_fallback_description(section)
                        else:
                            print(f"Error generating description: {response.status_code}")
                            descriptions[section] = self.get_fallback_description(section)
                            break
                            
                    except Exception as e:
                        print(f"Error generating description: {str(e)}")
                        descriptions[section] = self.get_fallback_description(section)
                        break
            
            return descriptions
            
        except Exception as e:
            print(f"Error in get_descriptions_from_t5: {str(e)}")
            return {
                'overview': self.get_fallback_description('overview'),
                'rooms': self.get_fallback_description('rooms'),
                'restaurant': self.get_fallback_description('restaurant')
            }
            
    def create_gradient_background(self, width, height):
        background = Image.new('RGB', (width, height), self.colors['primary'])
        overlay = Image.new('RGB', (width, height), self.colors['secondary'])
        mask = Image.new('L', (width, height))
        mask_data = []
        
        for y in range(height):
            mask_data.extend([int(255 * (1 - y/height))] * width)
        mask.putdata(mask_data)
        
        background.paste(overlay, (0, 0), mask)
        return background

    def draw_decorative_corner(self, draw, x, y, size, color):
        line_width = 2
        draw.line([(x, y), (x + size, y)], fill=color, width=line_width)
        draw.line([(x, y), (x, y + size)], fill=color, width=line_width)

    def add_text_to_image(self, draw, text, position, font, color=(20, 20, 20), max_width=40, add_bg=True, align='left'):
        if not text:
            return position[1]  # Return current y position if no text
            
        # Split text into words and create lines
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Try adding the word to the current line
            test_line = ' '.join(current_line + [word])
            # Use getbbox instead of getsize for better accuracy
            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]  # Right - Left = Width
            
            # If adding the word exceeds max_width, start a new line
            if line_width > max_width * 20:  # Multiply by 20 for better text wrapping
                if current_line:  # Only add non-empty lines
                    lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        
        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
        
        if not lines:  # If no lines were created
            return position[1]
            
        # Calculate dimensions for background
        line_spacing = font.size * 1.5
        text_height = len(lines) * line_spacing
        max_line_width = max([font.getbbox(line)[2] for line in lines])
        
        # Add semi-transparent background if requested
        if add_bg:
            padding = 20
            bg_bbox = [
                position[0] - padding,
                position[1] - padding,
                position[0] + max_line_width + padding,
                position[1] + text_height + padding
            ]
            draw.rectangle(bg_bbox, fill=(0, 0, 0, 128))
        
        # Draw text lines
        y = position[1]
        for line in lines:
            if align == 'center':
                line_width = font.getbbox(line)[2]
                x = position[0] + (max_line_width - line_width) // 2
            else:
                x = position[0]
            draw.text((x, y), line, font=font, fill=color)
            y += line_spacing
        
        return y  # Return the bottom position of the text

    def add_amenities_section(self, draw, start_x, start_y, width):
        # Add amenities title with elegant styling and extra line spacing
        amenities_title = "LUXURY AMENITIES"
        title_bbox = self.font_heading.getbbox(amenities_title)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = start_x + (width - title_width) // 2  # Center align
        self.add_text_to_image(draw, amenities_title, (title_x, start_y), self.font_heading, add_bg=False, color=self.colors['primary'])
        
        # Start position for amenities grid with extra line spacing
        grid_y = start_y + title_bbox[3] - title_bbox[1] + 120  # Increased from 80 to 120 for more spacing
        
        # Calculate grid layout for amenities
        amenities_per_row = 2  # Two columns
        row_height = 100  # Increased row height for better spacing
        col_width = width // amenities_per_row
        padding = 40  # Padding between columns
        
        # Add amenities in a grid with proper spacing
        for i, amenity in enumerate(self.amenities):
            row = i // amenities_per_row
            col = i % amenities_per_row
            
            # Calculate position with proper margins
            x = start_x + col * (col_width - padding) + padding  # Add padding between columns
            y = grid_y + row * row_height
            
            # Get text size for centering within column
            amenity_bbox = self.font_text.getbbox(amenity)
            amenity_width = amenity_bbox[2] - amenity_bbox[0]
            
            # Center text within column
            x = start_x + col * col_width + (col_width - amenity_width) // 2
            
            # Draw amenity text
            draw.text((x, y), amenity,
                     font=self.font_text,
                     fill=(20, 20, 20))  # Dark text for contrast
        
        # Return the bottom position of the amenities section
        return grid_y + ((len(self.amenities) + 1) // amenities_per_row) * row_height

    def add_pricing_section(self, draw, start_x, start_y, width):
        # Add pricing title
        pricing_title = "ACCOMMODATIONS"
        title_width = self.font_heading.getbbox(pricing_title)[2]
        title_x = (width - title_width) // 2
        self.add_text_to_image(draw, pricing_title, (title_x, start_y), self.font_heading, add_bg=False, color=self.colors['primary'])
        
        current_y = start_y + 60
        center_x = width // 2
        
        for room_type, price in self.pricing.items():
            # Add room type
            room_text = f"{room_type}"
            room_width = self.font_text.getbbox(room_text)[2]
            room_x = center_x - room_width - 20
            self.add_text_to_image(draw, room_text, (room_x, current_y), self.font_text, add_bg=False, color=self.colors['primary'])
            
            # Add price with accent color
            price_x = center_x + 20
            self.add_text_to_image(draw, price, (price_x, current_y), self.font_text, add_bg=False, color=self.colors['accent'])
            
            current_y += 50
        
        return current_y

    def add_social_media(self, draw, x, y, color):
        social_text = " | ".join([f"{platform}: {handle}" for platform, handle in self.social_media.items()])
        social_width = self.font_small.getbbox(social_text)[2]
        social_x = (x - social_width) // 2
        self.add_text_to_image(draw, social_text, (social_x, y), self.font_small, add_bg=False, color=color)

    def create_text_background(self, draw, text, font, x, y, padding_x=40, padding_y=20, wrap_width=None, max_width=None):
        """Create a dynamically sized background for text based on its content"""
        if wrap_width:
            text = textwrap.fill(text, width=wrap_width)
        
        # Calculate text dimensions for each line
        lines = text.split('\n')
        line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]
        line_widths = [font.getbbox(line)[2] - font.getbbox(line)[0] for line in lines]
        
        # Total height is sum of line heights
        text_height = sum(line_heights)
        # Width is the maximum line width
        text_width = max(line_widths)
        
        # Create background with padding
        bg_width = min(text_width + (padding_x * 2), max_width) if max_width else text_width + (padding_x * 2)
        bg_height = text_height + (padding_y * 2)
        
        # Create and paste background
        background = Image.new('RGBA', (bg_width, bg_height), (255, 255, 255, 180))
        
        return background, text, (x, y, bg_width, bg_height)

    def generate_brochure(self):
        """Generate the brochure"""
        width = self.width
        height = self.height
        
        # Create output directories if they don't exist
        for directory in ['generated_images', 'generated_brochures']:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {str(e)}")
                # Continue execution even if directory creation fails
                pass
        
        # Generate brochure based on layout
        if self.layout == 'default':
            brochure = self.generate_default_layout(width, height)
        elif self.layout == 'modern':
            brochure = self.generate_modern_layout(width, height)
        elif self.layout == 'classic':
            brochure = self.generate_classic_layout(width, height)
        elif self.layout == 'full_bleed':
            brochure = self.generate_full_bleed_layout(width, height)
        else:
            print("Invalid layout. Please choose from 'default', 'modern', 'classic', or 'full_bleed'.")
            return None

        # Save the brochure with proper error handling
        try:
            # Create a URL-safe filename by replacing spaces and special characters
            safe_hotel_name = self.hotel_name.replace(' ', '_').replace("'", '').replace('"', '').replace(',', '').replace('&', 'and')
            safe_hotel_name = ''.join(c for c in safe_hotel_name if c.isalnum() or c == '_')
            brochure_path = f'generated_brochures/{safe_hotel_name}_{self.layout}_brochure.pdf'
            
            # Convert PIL Image to PDF
            img_byte_arr = io.BytesIO()
            brochure.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Try to save the PDF
            try:
                c = canvas.Canvas(brochure_path, pagesize=(width, height))
                c.drawImage(ImageReader(io.BytesIO(img_byte_arr)), 0, 0, width, height)
                c.save()
                print(f"\nBrochure saved as: {brochure_path}")
            except Exception as e:
                # If saving to PDF fails, try saving as PNG instead
                fallback_path = f'generated_brochures/{safe_hotel_name}_{self.layout}_brochure.png'
                brochure.save(fallback_path, 'PNG')
                print(f"\nCould not save as PDF due to permissions. Saved as PNG instead: {fallback_path}")
            
            return brochure_path
            
        except Exception as e:
            print(f"Error saving brochure: {str(e)}")
            return None
        
    def generate_full_bleed_layout(self, width, height):
        # Create a new image with a white background
        image = Image.new('RGBA', (self.width, self.height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Add the main image as background
        if os.path.exists(self.exterior_image_path):
            bg_image = Image.open(self.exterior_image_path)
            bg_image = bg_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            image.paste(bg_image, (0, 0))
            
            # Add a darker gradient overlay for better text readability
            gradient = Image.new('RGBA', (self.width, self.height))
            gradient_draw = ImageDraw.Draw(gradient)
            for y in range(self.height):
                alpha = int(80 + (y / self.height) * 120)  # Increased opacity
                gradient_draw.line([(0, y), (self.width, y)], 
                                 fill=(0, 0, 0, alpha))
            image = Image.alpha_composite(image, gradient)
            draw = ImageDraw.Draw(image)
        
        # Add hotel name with adjusted spacing
        name_y = self.height // 8  # Moved up higher
        
        # Remove any extra 'The' from the display name
        display_name = self.hotel_name
        if display_name.startswith("'The "):
            display_name = display_name[5:-1]  # Remove 'The ' and the quote
        elif display_name.startswith('"The '):
            display_name = display_name[5:-1]  # Remove 'The ' and the quote
        elif display_name.startswith("The "):
            display_name = display_name[4:]  # Remove 'The ' without quotes
        
        # Remove any remaining quotes
        if display_name.startswith("'") or display_name.startswith('"'):
            display_name = display_name[1:]
        if display_name.endswith("'") or display_name.endswith('"'):
            display_name = display_name[:-1]
            
        name_text = display_name.upper()
        
        # Adjust font size for title to fit width
        font_size = 140
        while True:
            self.font_title = ImageFont.truetype(self.system_fonts['title'], font_size)
            name_bbox = self.font_title.getbbox(name_text)
            if name_bbox[2] - name_bbox[0] <= self.width - 100:  # Leave 50px margin on each side
                break
            font_size -= 5
        
        name_bbox = self.font_title.getbbox(name_text)
        name_width = name_bbox[2] - name_bbox[0]
        name_height = name_bbox[3] - name_bbox[1]
        name_x = (self.width - name_width) // 2
        
        # Add semi-transparent background for title
        title_padding = 80
        title_bg = Image.new('RGBA', (name_width + 2*title_padding, name_height + 2*title_padding), (255, 255, 255, 180))
        image.paste(title_bg, (name_x - title_padding, name_y - title_padding), title_bg)
        
        draw.text((name_x, name_y), name_text, 
                 font=self.font_title, 
                 fill=(20, 20, 20))
        
        # Add location with adjusted spacing
        location_text = self.location.upper()
        if location_text.startswith("THE "):
            location_text = location_text[4:]  # Remove "THE " from the start
        elif location_text == "THE":  # Remove standalone "THE"
            location_text = ""
        
        # Only proceed with location if we have text
        if location_text:
            location_bbox = self.font_heading.getbbox(location_text)
            location_width = location_bbox[2] - location_bbox[0]
            location_x = (self.width - location_width) // 2
            location_y = name_y + name_height + 60  # Reduced spacing between title and location
            
            # Create background for location
            loc_bg = Image.new('RGBA', (location_width + 160, location_bbox[3] + 40), (255, 255, 255, 180))
            image.paste(loc_bg, (location_x - 80, location_y - 10), loc_bg)
            draw.text((location_x, location_y), location_text, font=self.font_heading, fill=(20, 20, 20))
            
            # Adjust description position based on location
            desc_y = location_y + location_bbox[3] + 60  # Reduced spacing between location and description
        else:
            # If no location, put description closer to title
            desc_y = name_y + name_height + 90
        
        # Add description with adjusted spacing
        desc_text = self.descriptions.get('overview', 'Experience luxury redefined at our exclusive resort.')
        
        # Calculate maximum width for description (60% of total width)
        max_desc_width = int(self.width * 0.6)
        
        # Create dynamic background for main description
        desc_bg, wrapped_desc, (_, _, bg_width, bg_height) = self.create_text_background(
            draw,
            desc_text,
            self.font_text,
            0,
            desc_y,
            padding_x=60,
            padding_y=45,
            wrap_width=40,
            max_width=max_desc_width
        )
        
        # Center the background horizontally
        desc_x = (self.width - bg_width) // 2
        
        # Paste background and draw text
        image.paste(desc_bg, (desc_x, desc_y - 20), desc_bg)
        
        # Calculate text starting position to center within background
        text_bbox = self.font_text.getbbox(wrapped_desc.split('\n')[0])  # Get height of first line
        text_y = desc_y + (bg_height - (text_bbox[3] - text_bbox[1])) // 2 - 20  # Center text vertically
        
        # Draw the wrapped text with proper positioning
        draw.multiline_text((desc_x + 60, text_y), wrapped_desc,
                          font=self.font_text,
                          fill=(20, 20, 20),
                          align='center')
        
        # Add room and restaurant images with proper spacing
        image_width = (self.width - 480) // 2  # Increased margin between images from 360 to 480
        image_height = int(image_width * 0.6)  # Maintain aspect ratio
        
        # Room section
        room_x = 180
        room_y = desc_y + bg_height + 120
        
        if os.path.exists(self.room_image_path):
            room_image = Image.open(self.room_image_path)
            room_image = room_image.resize((image_width, image_height), Image.Resampling.LANCZOS)
            image.paste(room_image, (room_x, room_y))
            
            # Add room description with dynamic background
            room_desc = self.descriptions.get('room', 'Luxurious rooms with stunning ocean views.')
            room_desc_bg, wrapped_room_desc, (_, _, room_bg_width, room_bg_height) = self.create_text_background(
                draw,
                room_desc,
                self.font_small,
                0,
                0,
                padding_x=60,  # Increased padding for larger font
                padding_y=40,  # Increased padding for larger font
                wrap_width=20,  # Adjusted wrap width for larger font
                max_width=image_width
            )
            
            # Center the background under the image
            room_desc_y = room_y + image_height + 20
            room_desc_x = room_x + (image_width - room_bg_width) // 2
            
            # Paste background
            image.paste(room_desc_bg, (room_desc_x, room_desc_y), room_desc_bg)
            
            # Draw text centered within background
            text_x = room_desc_x + 40
            text_y = room_desc_y + 25
            draw.multiline_text((text_x, text_y), wrapped_room_desc,
                              font=self.font_small,
                              fill=(20, 20, 20),
                              align='center')
            
            room_desc_height = room_bg_height
        
        # Restaurant section with similar adjustments
        rest_x = self.width - image_width - 180
        rest_y = room_y
        
        if os.path.exists(self.restaurant_image_path):
            rest_image = Image.open(self.restaurant_image_path)
            rest_image = rest_image.resize((image_width, image_height), Image.Resampling.LANCZOS)
            image.paste(rest_image, (rest_x, rest_y))
            
            # Add restaurant description with dynamic background
            rest_desc = self.descriptions.get('dining')
            if not rest_desc or rest_desc.lower() == self.hotel_name.lower():
                rest_desc = "Experience world-class dining with local specialties and international cuisine in our signature restaurant."
            
            rest_desc_bg, wrapped_rest_desc, (_, _, rest_bg_width, rest_bg_height) = self.create_text_background(
                draw,
                rest_desc,
                self.font_small,
                0,
                0,
                padding_x=60,  # Increased padding for larger font
                padding_y=40,  # Increased padding for larger font
                wrap_width=20,  # Adjusted wrap width for larger font
                max_width=image_width
            )
            
            # Center the background under the image
            rest_desc_y = rest_y + image_height + 20
            rest_desc_x = rest_x + (image_width - rest_bg_width) // 2
            
            # Paste background
            image.paste(rest_desc_bg, (rest_desc_x, rest_desc_y), rest_desc_bg)
            
            # Draw text centered within background
            text_x = rest_desc_x + 40
            text_y = rest_desc_y + 25
            draw.multiline_text((text_x, text_y), wrapped_rest_desc,
                              font=self.font_small,
                              fill=(20, 20, 20),
                              align='center')
            
            rest_desc_height = rest_bg_height
        
        # Calculate max description height
        max_desc_height = max(room_desc_height, rest_desc_height) if 'room_desc_height' in locals() else 0
        
        # Add amenities section with adjusted spacing
        amenities_y = room_y + image_height + max_desc_height + 100
        amenities_width = int(self.width * 0.9)
        amenities_x = (self.width - amenities_width) // 2
        
        # Draw amenities title
        amenities_title = "LUXURY AMENITIES"
        title_font = self.font_heading
        title_bbox = title_font.getbbox(amenities_title)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        
        # Create background for amenities title
        title_bg = Image.new('RGBA', (title_width + 160, title_bbox[3] + 40), (255, 255, 255, 180))
        image.paste(title_bg, (title_x - 80, amenities_y - 10), title_bg)
        draw.text((title_x, amenities_y), amenities_title, font=title_font, fill=(20, 20, 20))
        
        # Adjust amenities layout
        amenities_start_y = amenities_y + title_bbox[3] + 30
        
        # Use the amenities generated by T5 instead of hardcoded list
        if not hasattr(self, 'amenities') or not self.amenities:
            self.amenities = [
                "24/7 Personal Butler Service",
                "Private Beach & Infinity Pool",
                "Luxury Yacht Charter",
                "World-Class Spa & Wellness",
                "Michelin-Star Dining",
                "Helicopter Transfer Service"
            ]
        
        # Calculate amenity box dimensions
        amenity_height = 60
        amenity_width = (amenities_width - 60) // 2
        amenity_padding = 20
        
        # Create and place amenity boxes in two columns
        for i, amenity in enumerate(self.amenities):
            is_right = i % 2
            row = i // 2
            
            # Calculate position
            x = amenities_x + (amenity_width + 60) * is_right
            y = amenities_start_y + (amenity_height + 20) * row
            
            # Create background
            amenity_bg = Image.new('RGBA', (amenity_width, amenity_height), (255, 255, 255, 180))
            image.paste(amenity_bg, (x, y), amenity_bg)
            
            # Draw checkbox
            checkbox_size = 24
            checkbox_x = x + amenity_padding
            checkbox_y = y + (amenity_height - checkbox_size) // 2
            checkbox = Image.new('RGBA', (checkbox_size, checkbox_size), (255, 255, 255, 0))
            checkbox_draw = ImageDraw.Draw(checkbox)
            checkbox_draw.rectangle([0, 0, checkbox_size-1, checkbox_size-1], outline=(20, 20, 20), width=2)
            image.paste(checkbox, (checkbox_x, checkbox_y), checkbox)
            
            # Draw text
            text_x = checkbox_x + checkbox_size + 15
            text_y = y + (amenity_height - title_bbox[3]) // 2
            draw.text((text_x, text_y), amenity, font=self.font_text, fill=(20, 20, 20))
        
        # Add contact information at the bottom
        contact_y = self.height - 100
        contact_text = f"RESERVATIONS: +1 (800) 123-4567  •  {self.contact_email}"
        contact_bbox = self.font_decorative.getbbox(contact_text)
        contact_width = contact_bbox[2] - contact_bbox[0]
        contact_x = (self.width - contact_width) // 2
        
        # Add contact background
        contact_padding = 20
        contact_bg = Image.new('RGBA', (contact_width + 2*contact_padding, contact_bbox[3] - contact_bbox[1] + 2*contact_padding), (255, 255, 255, 180))
        image.paste(contact_bg, (contact_x - contact_padding, contact_y - contact_padding), contact_bg)
        
        draw.text((contact_x, contact_y), contact_text,
                 font=self.font_decorative, fill=(20, 20, 20))
        
        # Save the brochure
        os.makedirs('generated_brochures', exist_ok=True)
        brochure_path = f'generated_brochures/{self.hotel_name}_{self.layout}_brochure.pdf'
        
        # Convert PIL Image to PDF
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Create PDF
        c = canvas.Canvas(brochure_path, pagesize=(self.width, self.height))
        c.drawImage(ImageReader(io.BytesIO(img_byte_arr)), 0, 0, self.width, self.height)
        c.save()
        
        print(f"\nBrochure saved as: {brochure_path}")
        return image
        
    def calculate_amenities_height(self, amenities):
        """Calculate total height needed for amenities section"""
        amenities_per_row = 2
        row_height = 100
        num_rows = (len(amenities) + amenities_per_row - 1) // amenities_per_row
        title_height = self.font_heading.getbbox("TEST")[3]  # Get approximate title height
        return title_height + (num_rows * row_height) + 60  # Add padding

    def generate_images(self):
        """Generate images using Stable Diffusion"""
        try:
            print("\nStarting image generation...")
            print(f"Hotel name: {self.hotel_name}")
            print(f"Location: {self.location}")
            
            # Generate images
            success = test_image_generation(
                hotel_name=self.hotel_name,
                location=self.location
            )
            
            if not success:
                raise Exception("Image generation failed")
            
            # Verify all required images exist
            required_images = [self.exterior_image_path, self.room_image_path, self.restaurant_image_path]
            print("\nVerifying generated images:")
            print(f"Looking for images in {os.path.abspath('generated_images')}")
            print(f"Directory contents:")
            for f in os.listdir('generated_images'):
                print(f"  {f}")
            
            for img_path in required_images:
                print(f"\nChecking {img_path}:")
                if not os.path.exists(img_path):
                    print(f"  File not found")
                    raise Exception(f"Image not found: {img_path}")
                try:
                    # Try to open the image to verify it's valid
                    print(f"  File exists, verifying...")
                    with Image.open(img_path) as img:
                        img.verify()
                    print(f"  File is valid")
                    print(f"  File size: {os.path.getsize(img_path)} bytes")
                except Exception as e:
                    print(f"  File verification failed: {str(e)}")
                    raise Exception(f"Invalid image file {img_path}: {str(e)}")
            
            print("Image generation and verification completed successfully")
                
        except Exception as e:
            print(f"Error in generate_images: {str(e)}")
            raise Exception(str(e))

def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Generate a single page brochure')
    parser.add_argument('--hotel_name', type=str, required=True, help='Name of the hotel')
    parser.add_argument('--location', type=str, required=True, help='Location of the hotel')
    parser.add_argument('--layout', type=str, default='full_bleed', help='Layout style (default, modern, classic, full_bleed)')
    args = parser.parse_args()
    
    print(f"\nGenerating brochure for {args.hotel_name} in {args.location}")
    
    # Create generator with specified layout
    generator = SinglePageBrochureGenerator(args.hotel_name, args.location, layout=args.layout)
    generator.generate_brochure()

if __name__ == "__main__":
    main()
