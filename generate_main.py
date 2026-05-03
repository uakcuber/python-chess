content = """from pygame import *
import pygame
import sys
import threading
import time
import requests

API_URL = "http://127.0.0.1:8000/state"

my_color = "white"
if len(sys.argv) > 1:
    my_color = sys.argv[1].lower()

class Tahta:
    def __init__(self):
        # boşluk 0 piyon 1 kale 2 at 3 fil 4 vezir 5 şah 6
        self.tahta = [
            [-2,-3,-4,-5,-6,-4,-3,-2],
            [-1,-1,-1,-1,-1,-1,-1,-1],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [1,1,1,1,1,1,1,1],
            [2,3,4,5,6,4,3,2]
            ]
        
        self.oyun_sirasi = "white"
        self.son_hamle = None
        self.rok_durumu = {
            "white": {"K": False, "R1": False, "R2": False},
            "black": {"K": False, "R1": False, "R2": False}
        }
        self.oyun_bitti = False
        self.kazanan = None

        threading.Thread(target=self.fetch_state_loop, daemon=True).start()

        self.taslar = {
            1:"piyon",
            2:"kale",
            3:"at",
            4:"fil",
            5:"vezir",
            6:"sah"
        }

        self.pieces = {
            'white': {'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙'},
            'black': {'K': '♚', 'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞', 'P': '♟'}
        }

    def fetch_state_loop(self):
        while True:
            try:
                response = requests.get(API_URL)
                if response.status_code == 200:
                    data = response.json()
                    self.tahta = data["tahta"]
                    self.oyun_sirasi = data["oyun_sirasi"]
                    self.son_hamle = data["son_hamle"]
                    self.rok_durumu = data["rok_durumu"]
            except:
                pass
            time.sleep(0.5)

    def push_state(self):
        try:
            state = {
                "tahta": self.tahta,
                "oyun_sirasi": self.oyun_sirasi,
                "son_hamle": self.son_hamle,
                "rok_durumu": self.rok_durumu
            }
            requests.post(API_URL, json=state)
        except:
            pass

    def tehdit_altinda_mi(self, row, col, saldiran_renk):
        # Rakip taşların bu (row, col) karesine saldırıp saldırmadığını kontrol eder
        for r in range(8):
            for c in range(8):
                tas = self.tahta[r][c]
                if tas == 0:
                    continue
                # Eğer taş saldıran renge aitse (beyaz için pozitif, siyah için negatif)
                tas_renk = "white" if tas > 0 else "black"
                if tas_renk == saldiran_renk:
                    tas_degeri = abs(tas)
                    # Piyon saldırısı
                    if tas_degeri == 1:
                        yon = -1 if saldiran_renk == "white" else 1
                        if r + yon == row and (c + 1 == col or c - 1 == col):
                            return True
                    # Kale saldırısı
                    elif tas_degeri == 2:
                        if r == row or c == col:
                            # Arada taş var mı kontrolü
                            engel_var = False
                            adim_r = 1 if row > r else (-1 if row < r else 0)
                            adim_c = 1 if col > c else (-1 if col < c else 0)
                            cr, cc = r + adim_r, c + adim_c
                            while cr != row or cc != col:
                                if self.tahta[cr][cc] != 0:
                                    engel_var = True
                                    break
                                cr += adim_r
                                cc += adim_c
                            if not engel_var: return True
                    # Fil saldırısı
                    elif tas_degeri == 4:
                        if abs(r - row) == abs(c - col):
                            engel_var = False
                            adim_r = 1 if row > r else -1
                            adim_c = 1 if col > c else -1
                            cr, cc = r + adim_r, c + adim_c
                            while cr != row and cc != col:
                                if self.tahta[cr][cc] != 0:
                                    engel_var = True
                                    break
                                cr += adim_r
                                cc += adim_c
                            if not engel_var: return True
                    # Vezir saldırısı
                    elif tas_degeri == 5:
                        if r == row or c == col or abs(r - row) == abs(c - col):
                            engel_var = False
                            adim_r = 1 if row > r else (-1 if row < r else 0)
                            adim_c = 1 if col > c else (-1 if col < c else 0)
                            cr, cc = r + adim_r, c + adim_c
                            while cr != row or cc != col:
                                if self.tahta[cr][cc] != 0:
                                    engel_var = True
                                    break
                                cr += adim_r
                                cc += adim_c
                            if not engel_var: return True
                    # At saldırısı
                    elif tas_degeri == 3:
                        if (abs(r - row) == 2 and abs(c - col) == 1) or (abs(r - row) == 1 and abs(c - col) == 2):
                            return True
                    # Şah saldırısı
                    elif tas_degeri == 6:
                        if abs(r - row) <= 1 and abs(c - col) <= 1:
                            return True
        return False

    def sah_konumu_bul(self, renk):
        istenen_sah = 6 if renk == "white" else -6
        for r in range(8):
            for c in range(8):
                if self.tahta[r][c] == istenen_sah:
                    return (r, c)
        return None

    def olasi_hamleleri_ver(self, row, col, oyun_sirasi, son_hamle):
        gecerli_kareler = []
        tas_degeri = self.tahta[row][col]
        
        if abs(tas_degeri) == 1:
            yon = -1 if oyun_sirasi == "white" else 1
            baslangic_satiri = 6 if oyun_sirasi == "white" else 1
            
            if 0 <= row + yon <= 7 and self.tahta[row + yon][col] == 0:
                gecerli_kareler.append((row + yon, col))
                if row == baslangic_satiri and self.tahta[row + (2 * yon)][col] == 0:
                    gecerli_kareler.append((row + (2 * yon), col))
                    
            if 0 <= row + yon <= 7:
                if col < 7 and self.tahta[row + yon][col + 1] != 0:
                    hedef_renk = "white" if self.tahta[row + yon][col + 1] > 0 else "black"
                    if hedef_renk != oyun_sirasi:
                        gecerli_kareler.append((row + yon, col + 1))
                if col > 0 and self.tahta[row + yon][col - 1] != 0:
                    hedef_renk = "white" if self.tahta[row + yon][col - 1] > 0 else "black"
                    if hedef_renk != oyun_sirasi:
                        gecerli_kareler.append((row + yon, col - 1))
                        
            if son_hamle:
                sr, sc, br, bc, stas = son_hamle[0], son_hamle[1], son_hamle[2], son_hamle[3], son_hamle[4]
                if abs(stas) == 1 and abs(br - sr) == 2 and br == row and abs(bc - col) == 1:
                    gecerli_kareler.append((row + yon, bc))
                    
        elif abs(tas_degeri) == 2:
            yonler = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for d_row, d_col in yonler:
                for i in range(1, 8):
                    yeni_row = row + d_row * i
                    yeni_col = col + d_col * i
                    if 0 <= yeni_row <= 7 and 0 <= yeni_col <= 7:
                        if self.tahta[yeni_row][yeni_col] == 0:
                            gecerli_kareler.append((yeni_row, yeni_col))
                        else:
                            hedef_renk = "white" if self.tahta[yeni_row][yeni_col] > 0 else "black"
                            if hedef_renk != oyun_sirasi:
                                gecerli_kareler.append((yeni_row, yeni_col))
                            break
                    else: break
                    
        elif abs(tas_degeri) == 3:
            yonler = [(-1,2), (1,2), (-2,1), (-2,-1), (2,1), (2,-1), (-1,-2), (1,-2)]
            for d_row, d_col in yonler:
                yeni_row = row + d_row
                yeni_col = col + d_col
                if 0 <= yeni_row <= 7 and 0 <= yeni_col <= 7:
                    if self.tahta[yeni_row][yeni_col] == 0:
                        gecerli_kareler.append((yeni_row, yeni_col))
                    else:
                        hedef_renk = "white" if self.tahta[yeni_row][yeni_col] > 0 else "black"
                        if hedef_renk != oyun_sirasi:
                            gecerli_kareler.append((yeni_row, yeni_col))

        elif abs(tas_degeri) == 4:
            yonler = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for d_row, d_col in yonler:
                for i in range(1, 8):
                    yeni_row = row + d_row * i
                    yeni_col = col + d_col * i
                    if 0 <= yeni_row <= 7 and 0 <= yeni_col <= 7:
                        if self.tahta[yeni_row][yeni_col] == 0:
                            gecerli_kareler.append((yeni_row, yeni_col))
                        else:
                            hedef_renk = "white" if self.tahta[yeni_row][yeni_col] > 0 else "black"
                            if hedef_renk != oyun_sirasi:
                                gecerli_kareler.append((yeni_row, yeni_col))
                            break
                    else: break

        elif abs(tas_degeri) == 5:
            yonler = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for d_row, d_col in yonler:
                for i in range(1, 8):
                    yeni_row = row + d_row * i
                    yeni_col = col + d_col * i
                    if 0 <= yeni_row <= 7 and 0 <= yeni_col <= 7:
                        if self.tahta[yeni_row][yeni_col] == 0:
                            gecerli_kareler.append((yeni_row, yeni_col))
                        else:
                            hedef_renk = "white" if self.tahta[yeni_row][yeni_col] > 0 else "black"
                            if hedef_renk != oyun_sirasi:
                                gecerli_kareler.append((yeni_row, yeni_col))
                            break
                    else: break
                    
        elif abs(tas_degeri) == 6:
            yonler = [(-1,-1), (-1,0), (-1,1), (0,1), (0,-1), (1,1), (1,0), (1,-1)]
            for d_row, d_col in yonler:
                yeni_row = row + d_row
                yeni_col = col + d_col 
                if 0 <= yeni_row <= 7 and 0<= yeni_col <= 7:
                    if self.tahta[yeni_row][yeni_col] == 0:
                        gecerli_kareler.append((yeni_row, yeni_col))
                    else:
                        hedef_renk = "white" if self.tahta[yeni_row][yeni_col] > 0 else "black"
                        if hedef_renk != oyun_sirasi:
                            gecerli_kareler.append((yeni_row, yeni_col))
            
            # Rok hamleleri
            if hasattr(self, 'rok_durumu'):
                rakip = "black" if oyun_sirasi == "white" else "white"
                k_row = 7 if oyun_sirasi == "white" else 0
                if row == k_row and col == 4 and not self.rok_durumu[oyun_sirasi]["K"] and not self.tehdit_altinda_mi(row, col, rakip):
                    # Kısa Rok (Sağ)
                    if not self.rok_durumu[oyun_sirasi]["R2"] and self.tahta[row][5] == 0 and self.tahta[row][6] == 0:
                        if not self.tehdit_altinda_mi(row, 5, rakip) and not self.tehdit_altinda_mi(row, 6, rakip):
                            gecerli_kareler.append((row, 6))
                    # Uzun Rok (Sol)
                    if not self.rok_durumu[oyun_sirasi]["R1"] and self.tahta[row][1] == 0 and self.tahta[row][2] == 0 and self.tahta[row][3] == 0:
                        if not self.tehdit_altinda_mi(row, 2, rakip) and not self.tehdit_altinda_mi(row, 3, rakip):
                            gecerli_kareler.append((row, 2))
                            
        return gecerli_kareler

    def draw(self):
        pygame.init()
        screen = pygame.display.set_mode((800, 800))
        calisiyor = True
        screen.fill((255,255,255))
        kare_renk = [(135, 206, 235), (65, 105, 225)]
        ind = 0
        font = pygame.font.SysFont("segoeuisymbol", 60)
        piece_map = {1: 'P', 2: 'R', 3: 'N', 4: 'B', 5: 'Q', 6: 'K'}
        self.secili_olan = None
        gecerli_kareler = [] # tuple
        
        while calisiyor:
            pygame.display.set_caption(f"Satranç - Sıra: {self.oyun_sirasi} - Sen: {my_color}")
            for olay in pygame.event.get():
                if olay.type == pygame.QUIT:
                    calisiyor = False
                if olay.type == pygame.MOUSEBUTTONDOWN and not self.oyun_bitti:
                    if self.oyun_sirasi != my_color:
                        continue # Sıra sizde değilse tıklamayı yoksay
                        
                    col = olay.pos[0] // 100
                    row = olay.pos[1] // 100
                    
                    # Tıklanan taşın rengini bul
                    tiklanan_renk = None
                    if self.tahta[row][col] > 0:
                        tiklanan_renk = "white"
                    elif self.tahta[row][col] < 0:
                        tiklanan_renk = "black"

                    if self.secili_olan is None:
                        # Sadece sırası gelen oyuncu kendi taşını seçebilir
                        if self.tahta[row][col] != 0 and tiklanan_renk == self.oyun_sirasi:
                            self.secili_olan = (row, col)
                            print(f"Secilen tas: satır {row}, sütun {col}")
                            gecerli_kareler = self.olasi_hamleleri_ver(row, col, self.oyun_sirasi, self.son_hamle)

                    else:
                        # Eğer yine kendi taşına tıklarsa seçimi ona geçir
                        if self.tahta[row][col] != 0 and tiklanan_renk == self.oyun_sirasi:
                            self.secili_olan = (row, col)
                            print(f"Secilen tas: satır {row}, sütun {col}")
                            gecerli_kareler = self.olasi_hamleleri_ver(row, col, self.oyun_sirasi, self.son_hamle)

                        elif (row,col) in gecerli_kareler: # Geçerli hamleyse oyna
                            print(f"Hedefe tasindi: satır {row}, sütun {col}")
                            kaynak_r, kaynak_c = self.secili_olan
                            tas_deg = self.tahta[kaynak_r][kaynak_c]
                            
                            # En Passant yeme işlemi
                            if abs(tas_deg) == 1 and col != kaynak_c and self.tahta[row][col] == 0:
                                self.tahta[kaynak_r][col] = 0 # Yandan yenen piyonu yok et
                                
                            # Rok taşıma işlemi
                            if abs(tas_deg) == 6 and abs(col - kaynak_c) == 2:
                                if col > kaynak_c: # Kısa rok (Sağdaki kale gelir)
                                    self.tahta[row][col-1] = self.tahta[row][7]
                                    self.tahta[row][7] = 0
                                else: # Uzun rok (Soldaki kale gelir)
                                    self.tahta[row][col+1] = self.tahta[row][0]
                                    self.tahta[row][0] = 0
                                    
                            # Rok haklarının bozulması
                            if abs(tas_deg) == 6:
                                self.rok_durumu[self.oyun_sirasi]["K"] = True
                            elif abs(tas_deg) == 2:
                                if kaynak_c == 0: self.rok_durumu[self.oyun_sirasi]["R1"] = True
                                elif kaynak_c == 7: self.rok_durumu[self.oyun_sirasi]["R2"] = True
                                
                            self.son_hamle = [kaynak_r, kaynak_c, row, col, tas_deg]
                            
                            self.tahta[row][col] = tas_deg
                            self.tahta[kaynak_r][kaynak_c] = 0
                            
                            # Otomatik Vezir Terfisi (Pawn Promotion)
                            if abs(self.tahta[row][col]) == 1:
                                if (self.oyun_sirasi == "white" and row == 0) or (self.oyun_sirasi == "black" and row == 7):
                                    self.tahta[row][col] = 5 if self.oyun_sirasi == "white" else -5
                                    
                            self.secili_olan = None
                            gecerli_kareler.clear()
                            
                            # Sırayı diğer oyuncuya geçir
                            self.oyun_sirasi = "black" if self.oyun_sirasi == "white" else "white"
                            
                            # Mat var mı kontrol et? (Sıra geçen oyuncunun hamlesi kaldı mı)
                            butun_hamleler = []
                            rakip_renk = "black" if self.oyun_sirasi == "white" else "white"
                            for r_ in range(8):
                                for c_ in range(8):
                                    t_ = self.tahta[r_][c_]
                                    if t_ != 0 and ("white" if t_ > 0 else "black") == self.oyun_sirasi:
                                        tas_hamleleri = self.olasi_hamleleri_ver(r_, c_, self.oyun_sirasi, self.son_hamle)
                                        # Bu hamleleri şah tehdidine göre filtrele
                                        for gr, gc in tas_hamleleri:
                                            # Hamleyi geçici yap
                                            gecici_hedef = self.tahta[gr][gc]
                                            self.tahta[gr][gc] = t_
                                            self.tahta[r_][c_] = 0

                                            # En passant geçici yeme
                                            en_passant_yendi = False
                                            if abs(t_) == 1 and gc != c_ and gecici_hedef == 0:
                                                gecici_ep_hedef = self.tahta[r_][gc]
                                                self.tahta[r_][gc] = 0
                                                en_passant_yendi = True

                                            sah_k = self.sah_konumu_bul(self.oyun_sirasi)
                                            if sah_k and not self.tehdit_altinda_mi(sah_k[0], sah_k[1], rakip_renk):
                                                butun_hamleler.append((r_, c_, gr, gc))

                                            # Hamleyi geri al
                                            self.tahta[r_][c_] = t_
                                            self.tahta[gr][gc] = gecici_hedef
                                            if en_passant_yendi:
                                                self.tahta[r_][gc] = gecici_ep_hedef
                                                
                            if len(butun_hamleler) == 0:
                                self.oyun_bitti = True
                                sah_k = self.sah_konumu_bul(self.oyun_sirasi)
                                if sah_k and self.tehdit_altinda_mi(sah_k[0], sah_k[1], rakip_renk):
                                    print("SAH MAT! Kazanan:", rakip_renk)
                                    self.kazanan = rakip_renk
                                else:
                                    print("PAT! Oyun Berabere.")
                                    self.kazanan = "Berabere"
                                    
                            # API'ye GÜNCEL DURUMU GÖNDER
                            threading.Thread(target=self.push_state).start()
                                        
                        else:
                            # Boş bir yere (veya geçersiz hedefe) tıklanırsa seçimi kaldır
                            self.secili_olan = None
                            gecerli_kareler.clear()
            
            # Seçili taş varsa, geçerli kareleri şah tehdidine göre filtrele
            if self.secili_olan is not None:
                legal_kareler = []
                rakip_renk = "black" if self.oyun_sirasi == "white" else "white"
                r_sec, c_sec = self.secili_olan
                for gr, gc in gecerli_kareler:
                    gecici_hedef = self.tahta[gr][gc]
                    gecici_kaynak = self.tahta[r_sec][c_sec]
                    self.tahta[gr][gc] = gecici_kaynak
                    self.tahta[r_sec][c_sec] = 0
                    
                    sah_k = self.sah_konumu_bul(self.oyun_sirasi)
                    if sah_k and not self.tehdit_altinda_mi(sah_k[0], sah_k[1], rakip_renk):
                        legal_kareler.append((gr, gc))
                        
                    self.tahta[r_sec][c_sec] = gecici_kaynak
                    self.tahta[gr][gc] = gecici_hedef
                gecerli_kareler = legal_kareler

            for i in range(8):
                for j in range(8):
                    ind = (i + j) % 2
                    pygame.draw.rect(screen, kare_renk[ind], (j * 100, i * 100, 100, 100))
                    
                    # Şah çekilmiş mi kontrol et ve öyleyse zeminini kırmızı yap
                    sah_k = self.sah_konumu_bul(self.oyun_sirasi)
                    rakip_renk = "black" if self.oyun_sirasi == "white" else "white"
                    if sah_k and i == sah_k[0] and j == sah_k[1] and self.tehdit_altinda_mi(sah_k[0], sah_k[1], rakip_renk):
                        pygame.draw.rect(screen, (255, 0, 0), (j * 100, i * 100, 100, 100))
                        
                    # Oyun bittiyse ve şah mat olduysa koyu kırmızı yap
                    if self.oyun_bitti and self.kazanan != "Berabere" and sah_k and i == sah_k[0] and j == sah_k[1] and ("white" if self.kazanan == "black" else "black") == self.oyun_sirasi:
                        pygame.draw.rect(screen, (139, 0, 0), (j * 100, i * 100, 100, 100))

                    if self.secili_olan == (i, j):
                        pygame.draw.rect(screen, (0, 255, 0), (j * 100, i * 100, 100, 100), 5) # Seçili olan yeşil çerçeve
                    elif (i, j) in gecerli_kareler:
                        pygame.draw.rect(screen, (255, 0, 0), (j * 100, i * 100, 100, 100), 5) # Gidebileceği yerler kırmızı çerçeve

            for i in range(8):
                for j in range(8):
                    piece_val = self.tahta[i][j]
                    if piece_val != 0:
                        color = "black" if piece_val < 0 else "white"
                        piece_char = piece_map[abs(piece_val)]
                        text_color = (255, 255, 255) if color == "white" else (0, 0, 0)
                        piece_surface = font.render(self.pieces[color][piece_char], True, text_color)
                        text_rect = piece_surface.get_rect(center=(j * 100 + 50, i * 100 + 50))
                        screen.blit(piece_surface, text_rect)

            pygame.display.flip()
        pygame.quit()

    def game(self):
        pass

if __name__ == '__main__':
    tahta = Tahta()
    tahta.draw()
"""

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
