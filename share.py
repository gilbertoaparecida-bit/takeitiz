import requests
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

class TicketGenerator:
    def __init__(self):
        # Fontes do Google Fonts
        self.FONT_BOLD_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
        self.FONT_REG_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
        self.FONT_BLACK_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Black.ttf"

        self.font_hero = self.get_font(self.FONT_BLACK_URL, 80)
        self.font_dest = self.get_font(self.FONT_BOLD_URL, 40)
        self.font_label = self.get_font(self.FONT_REG_URL, 20)
        self.font_sub = self.get_font(self.FONT_REG_URL, 16)
        self.font_logo = self.get_font(self.FONT_BOLD_URL, 24)

    def get_font(self, url, size):
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return ImageFont.truetype(io.BytesIO(resp.content), size)
        except Exception:
            return ImageFont.load_default()

    def format_brl(self, value, currency):
        # Lógica manual de formatação BR
        val_str = f"{value:,.2f}" # Ex: 1,200.50
        val_str = val_str.replace(',', 'X').replace('.', ',').replace('X', '.') # Ex: 1.200,50
        if currency == "BRL":
            return f"R$ {val_str}"
        elif currency == "EUR":
            return f"€ {val_str}"
        else:
            return f"$ {val_str}"

    def create_ticket(self, destination, total_value, daily_value, days, vibe, currency):
        W, H = 600, 900
        img = Image.new('RGB', (W, H), color='#FFFFFF')
        draw = ImageDraw.Draw(img)

        # 1. Background Header
        draw.rectangle([(0, 0), (W, 250)], fill='#1E88E5')
        
        # 2. Logo e Header
        draw.text((W/2, 60), "TakeItIz 🧳", font=self.font_logo, fill='#FFFFFF', anchor="mm")
        draw.text((W/2, 100), "ORÇAMENTO DE VIAGEM", font=self.font_sub, fill='#BBDEFB', anchor="mm")

        # 3. Card Branco
        card_margin = 40
        card_top = 180
        card_bottom = H - 60
        draw.rectangle(
            [(card_margin, card_top), (W - card_margin, card_bottom)], 
            fill='#FFFFFF', outline='#E0E0E0', width=1
        )

        # 4. Destino
        dest_text = destination.upper()
        wrapper = textwrap.TextWrapper(width=14) 
        dest_lines = wrapper.wrap(text=dest_text)

        cursor_y = card_top + 80
        line_height = 45
        for line in dest_lines:
            draw.text((W/2, cursor_y), line, font=self.font_dest, fill='#31333F', anchor="mm")
            cursor_y += line_height

        # Divisor
        cursor_y += 20
        draw.line([(100, cursor_y), (500, cursor_y)], fill='#F0F0F0', width=2)
        
        # 5. O Grande Número (BR Format)
        cursor_y += 60
        draw.text((W/2, cursor_y), "POR PESSOA / DIA", font=self.font_sub, fill='#9E9E9E', anchor="mm")
        
        cursor_y += 60
        daily_fmt = self.format_brl(daily_value, currency)
        draw.text((W/2, cursor_y), daily_fmt, font=self.font_hero, fill='#1E88E5', anchor="mm")

        # 6. Rodapé do Card
        cursor_y += 100
        draw.rectangle([(card_margin + 10, cursor_y), (W - card_margin - 10, cursor_y + 140)], fill='#F8F9FA')
        
        text_y = cursor_y + 35
        total_fmt = self.format_brl(total_value, currency)
        
        draw.text((W/2, text_y), f"INVESTIMENTO TOTAL ({days} DIAS)", font=self.font_sub, fill='#757575', anchor="mm")
        draw.text((W/2, text_y + 35), total_fmt, font=self.font_label, fill='#31333F', anchor="mm")
        draw.text((W/2, text_y + 70), f"Vibe: {vibe.replace('_', ' ').title()}", font=self.font_sub, fill='#1E88E5', anchor="mm")

        # 7. Rodapé App
        draw.text((W/2, H - 30), "Planejado com TakeItIz App", font=self.font_sub, fill='#BDBDBD', anchor="mm")

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
