import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

class TicketGenerator:
    def __init__(self):
        # SPRINT 1: OTIMIZAÇÃO DE ASSETS
        # Fontes lidas localmente para eliminar latência de rede.
        # Requer arquivos Roboto-Bold.ttf, Roboto-Regular.ttf, Roboto-Black.ttf na raiz.
        self.FONT_BOLD = "Roboto-Bold.ttf"
        self.FONT_REG = "Roboto-Regular.ttf"
        self.FONT_BLACK = "Roboto-Black.ttf"

        self.font_hero = self.get_font(self.FONT_BLACK, 80)
        self.font_dest = self.get_font(self.FONT_BOLD, 45)
        self.font_label = self.get_font(self.FONT_REG, 22)
        self.font_url = self.get_font(self.FONT_BOLD, 26)
        self.font_logo = self.get_font(self.FONT_BOLD, 28)

    def get_font(self, path, size):
        try:
            # Carregamento direto do disco (Instantâneo)
            return ImageFont.truetype(path, size)
        except OSError:
            # Fallback de segurança caso o arquivo não seja encontrado
            return ImageFont.load_default()

    def format_money(self, val, curr):
        s = f"{val:,.2f}".replace(',','X').replace('.',',').replace('X','.')
        sym = {"BRL": "R$", "USD": "$", "EUR": "€"}.get(curr, "$")
        return f"{sym} {s}"

    def create_ticket(self, destination, total, daily, days, vibe, currency):
        W, H = 600, 900
        # Fundo Azul Marca Takeitiz
        img = Image.new('RGB', (W, H), color='#1E88E5')
        draw = ImageDraw.Draw(img)

        # CARD BRANCO CENTRAL
        margin = 30
        top = 120
        bottom = H - 120
        draw.rectangle([(margin, top), (W-margin, bottom)], fill='#FFFFFF', outline=None)
        
        # 1. HEADER (Logo no topo azul)
        draw.text((W/2, 60), "Takeitiz 🧳", font=self.font_logo, fill='#FFFFFF', anchor="mm")

        # 2. CONTEÚDO NO CARD
        cursor = top + 80
        
        # Destino
        dest_lines = textwrap.wrap(destination.upper(), width=14)
        for line in dest_lines:
            draw.text((W/2, cursor), line, font=self.font_dest, fill='#333333', anchor="mm")
            cursor += 50
            
        cursor += 40
        draw.line([(150, cursor), (450, cursor)], fill='#EEEEEE', width=3)
        cursor += 60
        
        # Diária
        draw.text((W/2, cursor), "POR PESSOA / DIA", font=self.font_label, fill='#888888', anchor="mm")
        cursor += 50
        draw.text((W/2, cursor), self.format_money(daily, currency), font=self.font_hero, fill='#1E88E5', anchor="mm")
        
        # Total
        cursor += 120
        draw.rectangle([(margin+20, cursor), (W-margin-20, cursor+140)], fill='#F5F9FF')
        txt_y = cursor + 35
        draw.text((W/2, txt_y), f"TOTAL ({days} DIAS)", font=self.font_label, fill='#555555', anchor="mm")
        draw.text((W/2, txt_y+40), self.format_money(total, currency), font=self.font_url, fill='#333333', anchor="mm")
        draw.text((W/2, txt_y+80), f"Vibe: {vibe.title()}", font=self.font_label, fill='#1E88E5', anchor="mm")

        # 3. RODAPÉ DE GROWTH (Preto com URL amarela/branca)
        footer_h = 90
        draw.rectangle([(0, H - footer_h), (W, H)], fill='#212121')
        draw.text((W/2, H - (footer_h/2)), "Baixe agora: takeitiz.com.br", font=self.font_url, fill='#FFFFFF', anchor="mm")

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
