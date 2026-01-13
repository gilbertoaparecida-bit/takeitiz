import requests
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

class TicketGenerator:
    def __init__(self):
        self.FONT_BOLD_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
        self.FONT_REG_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
        self.FONT_ITALIC_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Italic.ttf"

        self.font_title = self.get_font(self.FONT_BOLD_URL, 36)
        self.font_label = self.get_font(self.FONT_REG_URL, 18)
        self.font_value = self.get_font(self.FONT_BOLD_URL, 48)
        self.font_small = self.get_font(self.FONT_REG_URL, 15)
        # Fonte do footer ainda carregada mas não usada no texto, mantive para não quebrar init se reutilizar
        self.font_footer = self.get_font(self.FONT_ITALIC_URL, 12)

    def get_font(self, url, size):
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return ImageFont.truetype(io.BytesIO(resp.content), size)
        except Exception:
            return ImageFont.load_default()

    def create_ticket(self, destination, total_value, daily_value, days, vibe, currency):
        img = Image.new('RGB', (600, 750), color='#F0F2F6')
        draw = ImageDraw.Draw(img)

        draw.rectangle([(50, 20), (550, 680)], fill='#FFFFFF', outline='#E0E0E0', width=2)
        
        # Cabeçalho
        draw.text((300, 70), "TakeItIz 🧳", font=self.font_label, fill='#31333F', anchor="mm")
        draw.text((300, 110), "SUA VIAGEM PARA", font=self.font_small, fill='#808495', anchor="mm")

        # Destino
        dest_text = destination.upper()
        wrapper = textwrap.TextWrapper(width=16)
        dest_lines = wrapper.wrap(text=dest_text)

        bbox = draw.textbbox((0, 0), "A", font=self.font_title)
        line_height = bbox[3] - bbox[1] + 10 

        current_y = 160
        for line in dest_lines:
            draw.text((300, current_y), line, font=self.font_title, fill='#31333F', anchor="mm")
            current_y += line_height

        current_y += 20

        # Valor Total
        draw.text((300, current_y), "INVESTIMENTO TOTAL", font=self.font_small, fill='#808495', anchor="mm")
        current_y += 50
        total_fmt = f"{currency} {total_value:,.2f}"
        draw.text((300, current_y), total_fmt, font=self.font_value, fill='#1E88E5', anchor="mm")
        current_y += 60

        # Detalhes
        draw.text((300, current_y), f"{days} dias • Vibe {vibe.title()}", font=self.font_small, fill='#31333F', anchor="mm")
        current_y += 60

        # Valor Diário
        draw.rectangle([(160, current_y), (440, current_y + 70)], fill='#E3F2FD')
        draw.text((300, current_y + 20), "POR PESSOA/DIA", font=self.font_small, fill='#1565C0', anchor="mm")
        daily_fmt = f"{currency} {daily_value:,.2f}"
        draw.text((300, current_y + 45), daily_fmt, font=self.font_label, fill='#1565C0', anchor="mm")

        # --- FIM DO CONTEÚDO (Rodapé removido conforme solicitado) ---
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
