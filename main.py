import sys
import re
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (QApplication, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QTreeWidget,QTreeWidgetItem, QPushButton)


#hata tanımlamaları
class SozcukselHata(Exception): pass
class SozdizimselHata(Exception): pass
class AnlamsalHata(Exception): pass
#abstract syntax tree düğüm sınıfı
class AstNode:
    def __init__(self, dugum_tipi, degeri=None, cocuklari=None):
        self.tip = dugum_tipi
        self.deger = degeri
        self.cocuklar = cocuklari if cocuklari is not None else []
    def __repr__(self):
        return f"AstNode({self.tip}, value={self.deger}, children={len(self.cocuklar)})"

#token sınıfı - kaynak kodundaki her bir kelime/operatör için oluşturulan yapı
class Token:
    def __init__(self, tip, deger, pozisyon):
        self.tip = tip
        self.deger = deger
        self.pozisyon = pozisyon
    def __repr__(self):
        return f'Token({self.tip}, {repr(self.deger)}, {self.pozisyon})'
#lexer sınıfı - kaynak kodunu tokenlere ayıran sınıf
class Lexer:
    def __init__(self):
        #token türleri ve bunların regex desenleri
        token_tanimlari = [
            ('STRING', r'(\"[^\"\n]*\"|\'[^\'\n]*\')'),
            ('NUMBER', r'\b\d+(\.\d+)?\b'),
            ('COMMENT', r'\#.*'),
            ('KEYWORD', r'\b(if|else|for|while|return|def)\b'),
            ('IDENT', r'\b[A-Za-z_][A-Za-z0-9_]*\b'),
            ('RELOP', r'(==|!=|<=|>=|<|>)'),
            ('ASSIGN_OP', r'='),
            ('OP', r'[+\-*/():,]'),
            ('NEWLINE', r'\n'),
            ('SKIP', r'\s+'),
            ('MISMATCH', r'.'),
        ]
        self.token_regex = re.compile('|'.join('(?P<%s>%s)' % cift for cift in token_tanimlari))
    def tokenlestir(self, kod):
        #kaynak kodunu tokenlere ayırır
        tokenler = []
        for eslesme in self.token_regex.finditer(kod):
            tip, deger, pozisyon = eslesme.lastgroup, eslesme.group(), eslesme.start()
            if tip == 'SKIP': continue
            if tip == 'MISMATCH': raise SozcukselHata(f"Tanımsız sembol '{deger}' pozisyon {pozisyon}")
            tokenler.append(Token(tip, deger, pozisyon))
        return tokenler
#parser sınıfı - tokenleri alıp ast oluşturan sınıf
class Parser:
    def __init__(self):
        self.tokenler = []
        self.pozisyon = 0
        self.scope_yigini = []
    def ayristir(self, tokenler):
        #token listesini alıp ast oluşturur
        self.tokenler = tokenler
        self.pozisyon = 0
        self.scope_yigini = []
        self.scope_gir()
        return self.programi_ayristir()
    def scope_gir(self):
        #yeni bir scope oluşturur
        self.scope_yigini.append(set())
    def scope_cik(self):
        #mevcut scopedan çıkar
        if self.scope_yigini: self.scope_yigini.pop()
    def mevcut_scope_ekle(self, isim):
        #mevcut scopea yeni bir isim ekler
        if self.scope_yigini: self.scope_yigini[-1].add(isim)
    def tanimli_mi(self, isim):
        #bir ismin tanımlı olup olmadığını kontrol eder
        for scope in reversed(self.scope_yigini):
            if isim in scope: return True
        return False
    def mevcut_token(self):
        #mevcut tokeni döndürür
        if self.pozisyon < len(self.tokenler): return self.tokenler[self.pozisyon]
        son_pozisyon = self.tokenler[-1].pozisyon + len(self.tokenler[-1].deger) if self.tokenler else 0
        return Token('EOF', '', son_pozisyon)
    def goz_at(self):
        #bir sonraki tokene bakar
        if self.pozisyon + 1 < len(self.tokenler): return self.tokenler[self.pozisyon + 1]
        return Token('EOF', '', 0)
    def tuket(self, token_tipi, token_degeri=None):
        #mevcut tokeni tüketir ve ilerler
        token = self.mevcut_token()
        if token.tip == token_tipi and (token_degeri is None or token.deger == token_degeri):
            self.pozisyon += 1
            return token
        beklenen = f"'{token_degeri}'" if token_degeri else token_tipi
        if token.tip == 'EOF':
            raise SozdizimselHata(f"Beklenen: {beklenen} ancak dosya sonuna ulaşıldı.")
        else:
            raise SozdizimselHata(
                f"Beklenen: '{beklenen}' ama bulunan: {repr(token.deger)} (pozisyon {token.pozisyon})")
    def programi_ayristir(self):
        #programı ifadelere ayırır
        ifadeler = []
        while self.mevcut_token().tip != 'EOF':
            if self.mevcut_token().tip in ('NEWLINE', 'COMMENT'):
                self.pozisyon += 1
                continue
            ifadeler.append(self.ifadeyi_ayristir())
        return AstNode('program', cocuklari=ifadeler)
    def ifadeyi_ayristir(self):
        #tek bir ifadeyi ayrıştırır
        while self.mevcut_token().tip in ('NEWLINE', 'COMMENT'): self.pozisyon += 1
        token = self.mevcut_token()
        if token.tip == 'IDENT':
            if self.goz_at().tip == 'ASSIGN_OP':
                return self.atamayi_ayristir()
            else:
                return self.hesaplamayi_ayristir()
        elif token.tip == 'KEYWORD':
            if token.deger == 'if': return self.if_ifadesini_ayristir()
            if token.deger == 'def': return self.def_ifadesini_ayristir()
            if token.deger == 'return':
                self.tuket('KEYWORD', 'return')
                donus_degeri = self.hesaplamayi_ayristir() if self.mevcut_token().tip not in ('NEWLINE', 'EOF','COMMENT') else None
                return AstNode('return_statement', cocuklari=[donus_degeri] if donus_degeri else [])
        if token.tip == 'EOF': return AstNode('empty')
        raise SozdizimselHata(f"Geçersiz ifade başlangıcı: {token.tip}")
    def blogu_ayristir(self):
        #kod bloğunu ayrıştırır
        self.scope_gir()
        ifade_listesi = []
        while self.mevcut_token().tip in ('NEWLINE', 'COMMENT'): self.pozisyon += 1
        if self.mevcut_token().tip != 'EOF' and not (
                self.mevcut_token().tip == 'KEYWORD' and self.mevcut_token().deger in ('else', 'def')):
            ifade_listesi.append(self.ifadeyi_ayristir())
        self.scope_cik()
        return AstNode('block', cocuklari=ifade_listesi)
    def if_ifadesini_ayristir(self):
        #if ifadesini ayrıştırır
        self.tuket('KEYWORD', 'if')
        kosul = self.hesaplamayi_ayristir()
        self.tuket('OP', ':')
        dogru_blogu = self.blogu_ayristir()
        yanlis_blogu = None
        while self.mevcut_token().tip in ('NEWLINE', 'COMMENT'): self.pozisyon += 1
        if self.mevcut_token().tip == 'KEYWORD' and self.mevcut_token().deger == 'else':
            self.tuket('KEYWORD', 'else')
            self.tuket('OP', ':')
            yanlis_blogu = self.blogu_ayristir()
        cocuklar = [kosul, dogru_blogu]
        if yanlis_blogu: cocuklar.append(yanlis_blogu)
        return AstNode('if_statement', cocuklari=cocuklar)
    def def_ifadesini_ayristir(self):
        #fonksiyon tanımını ayrıştırır
        self.tuket('KEYWORD', 'def')
        fonksiyon_adi = self.tuket('IDENT').deger
        self.mevcut_scope_ekle(fonksiyon_adi)
        self.tuket('OP', '(')
        self.scope_gir()
        parametreler = self.parametre_listesini_ayristir()
        self.tuket('OP', ')')
        self.tuket('OP', ':')
        govde = self.blogu_ayristir()
        return AstNode('function_def', degeri=fonksiyon_adi, cocuklari=[parametreler, govde])
    def atamayi_ayristir(self):
        #atama ifadesini ayrıştırır
        sol_dugum = AstNode('identifier', degeri=self.mevcut_token().deger)
        self.tuket('IDENT')
        self.tuket('ASSIGN_OP')
        sag_dugum = self.hesaplamayi_ayristir()
        self.mevcut_scope_ekle(sol_dugum.deger)
        return AstNode('assignment', degeri='=', cocuklari=[sol_dugum, sag_dugum])
    def parametre_listesini_ayristir(self):
        #fonksiyon parametrelerini ayrıştırır
        parametreler = []
        if self.mevcut_token().tip != 'OP' or self.mevcut_token().deger != ')':
            parametre_adi = self.tuket('IDENT').deger
            self.mevcut_scope_ekle(parametre_adi)
            parametreler.append(AstNode('parameter', degeri=parametre_adi))
            while self.mevcut_token().tip == 'OP' and self.mevcut_token().deger == ',':
                self.tuket('OP', ',')
                parametre_adi = self.tuket('IDENT').deger
                self.mevcut_scope_ekle(parametre_adi)
                parametreler.append(AstNode('parameter', degeri=parametre_adi))
        return AstNode('param_list', cocuklari=parametreler)
    def hesaplamayi_ayristir(self):
        #hesaplama ifadesini ayrıştırır
        return self.karsilastirmayi_ayristir()
    def karsilastirmayi_ayristir(self):
        #karşılaştırma ifadesini ayrıştırır
        dugum = self.toplama_cikarmayi_ayristir()
        while self.mevcut_token().tip == 'RELOP':
            op = self.tuket('RELOP').deger
            sag = self.toplama_cikarmayi_ayristir()
            dugum = AstNode('binary_op', degeri=op, cocuklari=[dugum, sag])
        return dugum
    def toplama_cikarmayi_ayristir(self):
        #toplama ve çıkarma işlemlerini ayrıştırır
        dugum = self.carpma_bolmeyi_ayristir()
        while self.mevcut_token().tip == 'OP' and self.mevcut_token().deger in ('+', '-'):
            op = self.tuket('OP', self.mevcut_token().deger).deger
            sag = self.carpma_bolmeyi_ayristir()
            dugum = AstNode('binary_op', degeri=op, cocuklari=[dugum, sag])
        return dugum
    def carpma_bolmeyi_ayristir(self):
        #çarpma ve bölme işlemlerini ayrıştırır
        dugum = self.carpani_ayristir()
        while self.mevcut_token().tip == 'OP' and self.mevcut_token().deger in ('*', '/'):
            op = self.tuket('OP', self.mevcut_token().deger).deger
            sag = self.carpani_ayristir()
            dugum = AstNode('binary_op', degeri=op, cocuklari=[dugum, sag])
        return dugum
    def carpani_ayristir(self):
        #çarpanları ayrıştırır
        token = self.mevcut_token()
        if token.tip == 'NUMBER': return AstNode('number', degeri=self.tuket('NUMBER').deger)
        if token.tip == 'STRING': return AstNode('string', degeri=self.tuket('STRING').deger)
        if token.tip == 'IDENT':
            if self.goz_at().tip == 'OP' and self.goz_at().deger == '(':
                return self.fonksiyon_cagrisini_ayristir()
            else:
                if not self.tanimli_mi(token.deger): raise AnlamsalHata(f"Tanımsız değişken: '{token.deger}'")
                return AstNode('identifier', degeri=self.tuket('IDENT').deger)
        if token.tip == 'OP' and token.deger == '(':
            self.tuket('OP', '(')
            dugum = self.hesaplamayi_ayristir()
            self.tuket('OP', ')')
            return dugum
        raise SozdizimselHata(f"İfade içinde beklenmeyen sembol: {token.tip}")
    def fonksiyon_cagrisini_ayristir(self):
        #fonksiyon çağrısını ayrıştırır
        fonksiyon_adi = self.tuket('IDENT').deger
        if not self.tanimli_mi(fonksiyon_adi): raise AnlamsalHata(f"Tanımsız fonksiyon: '{fonksiyon_adi}'")
        self.tuket('OP', '(')
        argumanlar = []
        if self.mevcut_token().tip != 'OP' or self.mevcut_token().deger != ')':
            argumanlar.append(self.hesaplamayi_ayristir())
            while self.mevcut_token().tip == 'OP' and self.mevcut_token().deger == ',':
                self.tuket('OP', ',')
                argumanlar.append(self.hesaplamayi_ayristir())
        self.tuket('OP', ')')
        return AstNode('function_call', degeri=fonksiyon_adi, cocuklari=argumanlar)
#ana uygulama penceresi sınıfı
class SyntaxHighlighter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerçek Zamanlı Vurgulayıcı")
        self.lexer = Lexer()
        self.parser = Parser()
        self.tokenler = []
        self.ast = None
#örnek kod tanımı
        self.ornek_kod = """#Deneme kodu
mesaj = "Deneme Yazısı" # Atama ve Metin
#Fonksiyon tanımı
def topla(sayi1, sayi2):
    # Anahtar kelime ve karşılaştırma
    if sayi1 > 0:
        return sayi1 + sayi2 # Return ifadesi
    else:
        return 0

#Fonksiyon çağrısı
sonuc = topla(10, 20.5)
#Aritmetik İşlemler
a=1
b=2
c=a*b
d=a/b
"""
        self.arayuzu_kur()
    def arayuzu_kur(self):
        #gui arayüzünü oluşturur
        self.resize(1000, 600)
        self.ayirici = QSplitter(Qt.Horizontal)
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Courier New", 12))
        self.editor.setStyleSheet("QTextEdit { background-color: #282c34; color: #abb2bf; }")
        self.editor.textChanged.connect(self.metin_degistiginde)
        self.agac_widget = QTreeWidget()
        self.agac_widget.setHeaderLabel("Lexical Analiz")
        self.agac_widget.setStyleSheet("QTreeWidget { background-color: #282c34; color: #abb2bf; border: none; }")
        self.ayirici.addWidget(self.editor)
        self.ayirici.addWidget(self.agac_widget)
        self.ayirici.setSizes([600, 400])
        self.hata_etiketi = QLabel()
        self.hata_etiketi.setStyleSheet("color: #e06c75;")
        ust_buton_duzeni = QHBoxLayout()
        self.lex_buton = QPushButton("Lexical Analiz")
        self.ast_buton = QPushButton("Sözdizimi Ağacı")
        self.deneme_buton = QPushButton("Örnek Kodu Yükle")
        ust_buton_duzeni.addWidget(self.lex_buton)
        ust_buton_duzeni.addWidget(self.ast_buton)
        ust_buton_duzeni.addWidget(self.deneme_buton)
        self.lex_buton.clicked.connect(self.lexical_agaci_goster)
        self.ast_buton.clicked.connect(self.ast_agacini_goster)
        self.deneme_buton.clicked.connect(self.ornek_kodu_yukle)
        ana_duzen = QVBoxLayout()
        ana_duzen.addLayout(ust_buton_duzeni)
        ana_duzen.addWidget(self.ayirici, 1)
        ana_duzen.addWidget(self.hata_etiketi, 0)
        self.setLayout(ana_duzen)
        self.zamanlayici = QTimer()
        self.zamanlayici.setInterval(300)
        self.zamanlayici.setSingleShot(True)
        self.zamanlayici.timeout.connect(self.vurgula_ve_ayristir)

    def vurgula_ve_ayristir(self):
        #metni vurgular ve ayrıştırır
        kod = self.editor.toPlainText()
        self.hata_etiketi.clear()
        try:
            self.tokenler = self.lexer.tokenlestir(kod)
            self.tokenleri_vurgula()
            self.ast = self.parser.ayristir(self.tokenler) if self.tokenler else None
            self.hata_etiketi.setText("No syntax or semantic errors found.")
        except (SozcukselHata, SozdizimselHata, AnlamsalHata) as e:
            self.ast = None
            hata_tipi = "Lexical Error" if isinstance(e, SozcukselHata) else "Syntax Error"if isinstance(e,SozdizimselHata) else "Semantic Error"
            self.hata_etiketi.setText(f"{hata_tipi}: {e}")
        except Exception as e:
            self.ast = None
            self.hata_etiketi.setText(f"Unexpected Error: {e}")
        baslik = self.agac_widget.headerItem()
        if baslik and baslik.text(0) == "Sözdizimi Ağacı":
            self.ast_agacini_goster()
        else:
            self.lexical_agaci_goster()
    def ornek_kodu_yukle(self):
        #örnek kodu editöre yükler
        self.editor.setText(self.ornek_kod)
    def metin_degistiginde(self):
        #metin değiştiğinde zamanlayıcıyı başlatır
        self.zamanlayici.start()
    def tum_formatlamayi_temizle(self):
        #tüm metin formatlamasını temizler
        imlec = self.editor.textCursor()
        imlec.select(QTextCursor.Document)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#abb2bf"))
        imlec.setCharFormat(fmt)
        imlec.clearSelection()
    def tokenleri_vurgula(self):
        #tokenleri renklendirir
        imlec = self.editor.textCursor()
        pozisyon = imlec.position()
        imlec.beginEditBlock()
        self.tum_formatlamayi_temizle()
        renkler = {'KEYWORD': "#a8326f",'NUMBER': "#3ca374",'STRING': "#f2b632",'COMMENT': "#7461b2",'IDENT': "#e07b5c",'OP': "#4aa8e0",'RELOP': "#d14d7a",'ASSIGN_OP': "#3498db"}
        for token in self.tokenler:
            fmt = QTextCharFormat()
            renk_kodu = renkler.get(token.tip)
            if renk_kodu:
                fmt.setForeground(QColor(renk_kodu))
            if token.tip == 'KEYWORD':
                fmt.setFontWeight(QFont.Bold)
            if token.tip == 'COMMENT':
                fmt.setFontItalic(True)
            imlec.setPosition(token.pozisyon)
            imlec.setPosition(token.pozisyon + len(token.deger), QTextCursor.KeepAnchor)
            imlec.setCharFormat(fmt)
        imlec.endEditBlock()
        yeni_imlec = self.editor.textCursor()
        yeni_imlec.setPosition(pozisyon)
        self.editor.setTextCursor(yeni_imlec)

    def lexical_agaci_goster(self):
        #lexical analizi gösterir
        self.agac_widget.setHeaderLabel("Lexical Analiz")
        self.agac_widget.clear()
        if not self.tokenler: return
        for token in self.tokenler:
            if token.tip not in ('NEWLINE', 'COMMENT', 'SKIP'):
                QTreeWidgetItem(self.agac_widget, [f"{token.tip}: {repr(token.deger)}"])

    def ast_agacini_goster(self):
        #ast ağacını gösterir
        self.agac_widget.setHeaderLabel("Sözdizimi Ağacı")
        self.agac_widget.clear()
        if self.ast:
            self._ast_agacini_doldur(self.agac_widget, self.ast)
            self.agac_widget.expandAll()

    def _ast_agacini_doldur(self, ebeveyn_widget, dugum):
        #ast ağacını doldurur
        if dugum.tip == 'empty': return
        etiket = dugum.tip
        if dugum.deger is not None: etiket += f": {repr(dugum.deger)}"
        agac_ogesi = QTreeWidgetItem(ebeveyn_widget, [etiket])
        for cocuk in dugum.cocuklar:
            if cocuk:
                self._ast_agacini_doldur(agac_ogesi, cocuk)


#uygulama başlatma kodu
if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = SyntaxHighlighter()
    pencere.show()
    sys.exit(app.exec_())
