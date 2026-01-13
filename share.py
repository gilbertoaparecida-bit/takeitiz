import requests
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

class TicketGenerator:
    def __init__(self):
        # Fontes do Google Fonts (Cacheável se necessário)
        self.FONT_BOLD_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
        self.FONT_REG_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
        self.FONT_BLACK_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Black.ttf"

        # Carregamento seguro
        self.font_hero = self.get_font(self.FONT_BLACK_URL, 80)  # Para o valor diário
        self.font_dest = self.get_font(self.FONT_BOLD_URL, 40)   # Para o destino
        self.font_label = self.get_font(self.FONT_REG_URL, 20)   # Labels gerais
        self.font_sub = self.get_font(self.FONT_REG_URL, 16)     # Detalhes pequenos
        self.font_logo = self.get_font(self.FONT_BOLD_URL, 24)   # Logo TakeItIz

    def get_font(self, url, size):
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return ImageFont.truetype(io.BytesIO(resp.content), size)
        except Exception:
            return ImageFont.load_default()

    def create_ticket(self, destination, total_value, daily_value, days, vibe, currency):
        # Tamanho Story-Friendly (Vertical)
        W, H = 600, 900
        img = Image.new('RGB', (W, H), color='#FFFFFF')
        draw = ImageDraw.Draw(img)

        # 1. Background Header (Topo colorido)
        draw.rectangle([(0, 0), (W, 250)], fill='#1E88E5')
        
        # 2. Logo e Header
        draw.text((W/2, 60), "TakeItIz 🧳", font=self.font_logo, fill='#FFFFFF', anchor="mm")
        draw.text((W/2, 100), "ORÇAMENTO DE VIAGEM", font=self.font_sub, fill='#BBDEFB', anchor="mm")

        # 3. Card Branco Central (Simulando um ticket físico)
        card_margin = 40
        card_top = 180
        card_bottom = H - 60
        draw.rectangle(
            [(card_margin, card_top), (W - card_margin, card_bottom)], 
            fill='#FFFFFF', outline='#E0E0E0', width=1
        )
        # Sombra fake (opcional, desenhando retângulo cinza atrás antes)
        
        # 4. Destino (Tratamento para nomes longos)
        dest_text = destination.upper()
        # Wrapper ajustado para caber no card (aprox 14 chars com fonte 40px)
        wrapper = textwrap.TextWrapper(width=14) 
        dest_lines = wrapper.wrap(text=dest_text)

        cursor_y = card_top + 80
        
        # Ajuste dinâmico: se tiver muitas linhas, diminui entrelinha
        line_height = 45
        for line in dest_lines:
            draw.text((W/2, cursor_y), line, font=self.font_dest, fill='#31333F', anchor="mm")
            cursor_y += line_height

        # Divisor
        cursor_y += 20
        draw.line([(100, cursor_y), (500, cursor_y)], fill='#F0F0F0', width=2)
        
        # 5. O Grande Número (Por Pessoa/Dia)
        cursor_y += 60
        draw.text((W/2, cursor_y), "POR PESSOA / DIA", font=self.font_sub, fill='#9E9E9E', anchor="mm")
        
        cursor_y += 60
        daily_fmt = f"{currency} {daily_value:,.0f}"
        draw.text((W/2, cursor_y), daily_fmt, font=self.font_hero, fill='#1E88E5', anchor="mm")

        # 6. Rodapé do Card (Total e Detalhes)
        cursor_y += 100
        # Fundo cinza claro para o bloco de detalhes
        draw.rectangle([(card_margin + 10, cursor_y), (W - card_margin - 10, cursor_y + 140)], fill='#F8F9FA')
        
        text_y = cursor_y + 35
        total_fmt = f"{currency} {total_value:,.2f}"
        
        draw.text((W/2, text_y), f"INVESTIMENTO TOTAL ({days} DIAS)", font=self.font_sub, fill='#757575', anchor="mm")
        draw.text((W/2, text_y + 35), total_fmt, font=self.font_label, fill='#31333F', anchor="mm")
        draw.text((W/2, text_y + 70), f"Vibe: {vibe.replace('_', ' ').title()}", font=self.font_sub, fill='#1E88E5', anchor="mm")

        # 7. Rodapé App
        draw.text((W/2, H - 30), "Planejado com TakeItIz App", font=self.font_sub, fill='#BDBDBD', anchor="mm")

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
