from PIL import Image, ImageDraw, ImageFont
import io
import textwrap # Importante para quebrar o texto do destino

class TicketGenerator:
    def __init__(self):
        # Tenta carregar fontes do sistema, senão usa a padrão
        try:
            self.font_title = ImageFont.truetype("arialbd.ttf", 40) # Bold para cidade
            self.font_label = ImageFont.truetype("arial.ttf", 20)
            self.font_value = ImageFont.truetype("arialbd.ttf", 50) # Bold para valor
            self.font_small = ImageFont.truetype("arial.ttf", 16)
            self.font_footer = ImageFont.truetype("ariali.ttf", 14) # Itálico para footer
        except IOError:
            self.font_title = ImageFont.load_default()
            self.font_label = ImageFont.load_default()
            self.font_value = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_footer = ImageFont.load_default()

    def create_ticket(self, destination, total_value, daily_value, days, vibe, currency):
        # Cria a imagem base (Fundo cinza claro)
        img = Image.new('RGB', (600, 750), color='#F0F2F6') # Aumentei um pouco a altura
        draw = ImageDraw.Draw(img)

        # Desenha o "Ticket" branco no centro
        draw.rectangle([(50, 20), (550, 680)], fill='#FFFFFF', outline='#E0E0E0', width=2)
        
        # --- Conteúdo ---
        
        # Cabeçalho
        draw.text((300, 60), "TakeItIz 🧳", font=self.font_title, fill='#31333F', anchor="mm")
        draw.text((300, 110), "SUA VIAGEM PARA", font=self.font_label, fill='#808495', anchor="mm")

        # --- CORREÇÃO: DESTINO COM QUEBRA AUTOMÁTICA DE LINHA ---
        dest_text = destination.upper()
        # Configura para quebrar a cada 18 caracteres (ajuste fino para a largura do ticket)
        wrapper = textwrap.TextWrapper(width=18)
        dest_lines = wrapper.wrap(text=dest_text)

        # Desenha cada linha do destino
        y_pos = 160
        for line in dest_lines:
            draw.text((300, y_pos), line, font=self.font_title, fill='#31333F', anchor="mm")
            y_pos += 45 # Espaçamento entre as linhas do nome da cidade

        # Ajusta a posição Y para o próximo elemento baseado em quantas linhas a cidade ocupou
        current_y = y_pos + 40

        # Valor Total
        draw.text((300, current_y), "INVESTIMENTO TOTAL", font=self.font_label, fill='#808495', anchor="mm")
        current_y += 60
        total_fmt = f"{currency} {total_value:,.2f}"
        draw.text((300, current_y), total_fmt, font=self.font_value, fill='#1E88E5', anchor="mm")
        current_y += 70

        # Detalhes
        draw.text((300, current_y), f"{days} dias • Vibe {vibe.title()}", font=self.font_small, fill='#31333F', anchor="mm")
        current_y += 60

        # Caixa do Valor Diário
        draw.rectangle([(150, current_y), (450, current_y + 80)], fill='#E3F2FD')
        draw.text((300, current_y + 25), "POR PESSOA/DIA", font=self.font_small, fill='#1565C0', anchor="mm")
        daily_fmt = f"{currency} {daily_value:,.2f}"
        draw.text((300, current_y + 55), daily_fmt, font=self.font_label, fill='#1565C0', anchor="mm")

        # Rodapé
        draw.text((300, 650), "Planejado com Inteligência Artificial", font=self.font_footer, fill='#9E9E9E', anchor="mm")
        
        # Salva em memória
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
