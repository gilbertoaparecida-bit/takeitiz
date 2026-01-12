from PIL import Image, ImageDraw, ImageFont
import io

class TicketGenerator:
    def __init__(self):
        # Cores da Marca
        self.COLOR_BG = "#F0F2F6"      # Fundo Off-white
        self.COLOR_CARD = "#FFFFFF"    # Cartão Branco
        self.COLOR_PRIMARY = "#FF4B4B" # Vermelho Streamlit
        self.COLOR_TEXT = "#31333F"    # Cinza Escuro
        self.COLOR_ACCENT = "#1E88E5"  # Azul Link

    def create_ticket(self, destination, total_value, daily_value, days, vibe, currency):
        # 1. Configurações da Imagem (Formato Instagram Stories 9:16)
        W, H = 540, 960 
        img = Image.new('RGB', (W, H), color=self.COLOR_BG)
        draw = ImageDraw.Draw(img)

        # 2. Desenha o "Cartão"
        margin = 40
        card_top = 150
        card_bottom = H - 150
        draw.rectangle(
            [(margin, card_top), (W - margin, card_bottom)], 
            fill=self.COLOR_CARD, 
            outline="#E0E0E0", 
            width=2
        )

        # 3. Fontes (Fallback para padrão se não tiver TTF)
        try:
            font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
            font_label = ImageFont.truetype("DejaVuSans.ttf", 20)
            font_value = ImageFont.truetype("DejaVuSans-Bold.ttf", 50)
        except:
            font_title = ImageFont.load_default()
            font_label = ImageFont.load_default()
            font_value = ImageFont.load_default()

        # 4. Textos e Layout
        # Título
        draw.text((W/2, 80), "TakeItIz 🧳", font=font_title, fill=self.COLOR_TEXT, anchor="mm")
        
        # Destino
        draw.text((W/2, card_top + 60), "SUA VIAGEM PARA", font=font_label, fill="#888888", anchor="mm")
        draw.text((W/2, card_top + 100), destination.upper(), font=font_title, fill=self.COLOR_TEXT, anchor="mm")
        
        # Linha
        draw.line([(margin+20, card_top + 150), (W-margin-20, card_top + 150)], fill="#EEEEEE", width=2)
        
        # Valor Total
        draw.text((W/2, card_top + 200), "INVESTIMENTO TOTAL", font=font_label, fill="#888888", anchor="mm")
        draw.text((W/2, card_top + 250), f"{currency} {total_value:,.2f}", font=font_value, fill=self.COLOR_ACCENT, anchor="mm")
        
        # Detalhes
        draw.text((W/2, card_top + 320), f"{days} dias • Vibe {vibe}", font=font_label, fill=self.COLOR_TEXT, anchor="mm")
        
        # Box Azulzinho
        draw.rectangle(
            [(margin+40, card_top + 380), (W-margin-40, card_top + 460)],
            fill="#E3F2FD" 
        )
        draw.text((W/2, card_top + 400), "POR PESSOA/DIA", font=font_label, fill=self.COLOR_ACCENT, anchor="mm")
        draw.text((W/2, card_top + 430), f"{currency} {daily_value:,.2f}", font=font_label, fill=self.COLOR_ACCENT, anchor="mm")

        # Rodapé
        draw.text((W/2, card_bottom - 50), "Planejado com Inteligência", font=font_label, fill="#888888", anchor="mm")

        # 5. Exporta bytes
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        return byte_im
