# -*- coding: cp1254 -*-
class KantarHatasi(Exception):
    def __init__(self, baslik, kontroller=None, teknik_detay=None):
        super().__init__(baslik)
        self.baslik = baslik
        self.kontroller = kontroller or []
        self.teknik_detay = teknik_detay

    def kullanici_mesaji(self):
        satirlar = ["Kantar hatasi: " + self.baslik]
        if self.kontroller:
            satirlar.append("Kontrol edilecekler:")
            for kontrol in self.kontroller:
                satirlar.append("- " + kontrol)
        if self.teknik_detay:
            satirlar.append("Teknik detay: " + self.teknik_detay)
        return "\n".join(satirlar)
