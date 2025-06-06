# Proje Teknik Dokümantasyonu: Gerçek Zamanlı Sözdizimi Analiz Aracı

## İçindekiler
1. [Giriş ve Proje Amacı](#1-giriş-ve-proje-amacı)
2. [Sistem Mimarisi ve Tasarım Seçimleri](#2-sistem-mimarisi-ve-tasarım-seçimleri)
   - [Sınıf Yapısı](#sınıf-yapısı)
   - [Veri Akışı](#veri-akışı)
3. [Sözcüksel Analiz (Lexical Analysis)](#3-sözcüksel-analiz-lexical-analysis)
   - [Seçilen Yöntem: State Diagram & Program Implementation](#seçilen-yöntem)
   - [Token Tanımları ve `Lexer` Sınıfı](#token-tanımları-ve-lexer-sınıfı)
4. [Sözdizimsel ve Anlamsal Analiz (Parsing & Semantic Analysis)](#4-sözdizimsel-ve-anlamsal-analiz)
   - [Seçilen Yöntem (Parser): Top-Down Recursive Descent](#seçilen-yöntem-parser)
   - [Soyut Sözdizimi Ağacı (AST)](#soyut-sözdizimi-ağacı-ast)
   - [Anlamsal Kontroller ve Kapsam Yönetimi](#anlamsal-kontroller-ve-kapsam-yönetimi)
   - [Dilbilgisi (Grammar) Kuralları](#dilbilgisi-grammar-kuralları)
5. [Grafiksel Kullanıcı Arayüzü (GUI)](#5-grafiksel-kullanıcı-aracephesi-gui)
   - [Bileşenler ve `SyntaxHighlighter` Sınıfı](#bileşenler-ve-syntaxhighlighter-sınıfı)
   - [Sözdizimi Vurgulama Mantığı](#sözdizimi-vurgulama-mantığı)
   - [Gerçek Zamanlı Güncelleme Mekanizması](#gerçek-zamanlı-güncelleme-mekanizması)
6. [Hata Yönetimi](#6-hata-yönetimi)

---

## 1. Giriş ve Proje Amacı

Bu proje, bir programlama dilinin derleyici veya yorumlayıcı tarafından nasıl işlendiğini gösteren interaktif bir araç geliştirmeyi amaçlamaktadır. Proje, derleyici tasarımının üç temel ön yüz (front-end) aşamasını uygular:
1.  **Sözcüksel Analiz:** Metin kodunu token'lara ayırma.
2.  **Sözdizimsel Analiz:** Token dizisinin dilin gramerine uygunluğunu kontrol etme ve yapısal bir ağaç (AST) oluşturma.
3.  **Anlamsal Analiz:** Kodun mantıksal tutarlılığını (örn: tanımsız değişkenler) denetleme.

Bu süreçler, kullanıcıya gerçek zamanlı olarak sunulan bir sözdizimi vurgulayıcı ve analiz ağaçları aracılığıyla görselleştirilir.

## 2. Sistem Mimarisi ve Tasarım Seçimleri

Proje, sorumlulukların net bir şekilde ayrıldığı nesne yönelimli bir tasarıma sahiptir. Bu, kodun modülerliğini, okunabilirliğini ve genişletilebilirliğini artırır.

### Sınıf Yapısı
-   **`Lexer`:** Kaynak kodunu alıp token listesi üretmekten sorumludur. Durum bilgisi tutmaz, her çağrıda yeni bir analiz yapar.
-   **`Parser`:** `Lexer`'dan aldığı token listesini işler. Kendi içinde pozisyon (`self.pozisyon`) ve kapsam (`self.kapsam_yigini`) gibi durum bilgilerini yönetir. Bir AST üretir ve anlamsal kontroller yapar.
-   **`SyntaxHighlighter` (QWidget):** Ana GUI penceresidir. `Lexer` ve `Parser` nesnelerini barındırır, kullanıcı etkileşimlerini yönetir ve analiz sonuçlarını (renklendirme, ağaçlar, hatalar) arayüzde gösterir.
-   **Yardımcı Sınıflar:** `Token`, `AstNode` ve özel hata sınıfları (`SozcukselHata`, `SozdizimselHata`, `AnlamsalHata`) veri yapılarını ve hata durumlarını modellemek için kullanılır.

### Veri Akışı
1.  Kullanıcı `QTextEdit`'e kod yazar.
2.  `textChanged` sinyali `QTimer`'ı tetikler.
3.  Zamanlayıcı dolunca `vurgula_ve_ayristir` metodu çalışır.
4.  Metin, `Lexer.tokenlestir()`'e gönderilir ve `tokenlar` listesi alınır.
5.  `tokenlar` listesi, `tokenlari_vurgula()` ile metni renklendirmek için kullanılır.
6.  `tokenlar` listesi, `Parser.ayristir()`'a gönderilir.
7.  `Parser`, bir **AST** üretir veya bir **hata** fırlatır.
8.  Sonuç (AST veya hata), arayüzdeki `QTreeWidget` ve `QLabel` üzerinde gösterilir.

## 3. Sözcüksel Analiz (Lexical Analysis)

### Seçilen Yöntem
Projede, **"State Diagram & Program Implementation"** yaklaşımı benimsenmiştir. Dilin token yapısı, düzenli ifadeler (regex) kullanılarak bir **formal tanım (state diagram)** olarak belirtilmiştir. Bu tanımlar, Python'un `re` modülü (programmatic implementation) aracılığıyla verimli bir şekilde işlenir. Bu yöntem, esnekliği ve standart kütüphanelerle kolayca uygulanabilmesi nedeniyle seçilmiştir.

### Token Tanımları ve `Lexer` Sınıfı
`Lexer` sınıfının kurucu metodunda, tanınacak tüm token türleri ve desenleri bir liste halinde tutulur.
```python
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


SKIP kuralı boşlukları yoksaymak, MISMATCH kuralı ise dilde olmayan geçersiz sembolleri yakalamak için bir güvenlik ağı olarak kullanılır.

4. Sözdizimsel ve Anlamsal Analiz
Seçilen Yöntem (Parser)

Parser için "Top-Down" yaklaşım ve bu yaklaşımın yaygın bir uygulaması olan Recursive Descent Parser (Özyinelemeli İnişli Ayrıştırıcı) tekniği kullanılmıştır. Bu yöntem, gramer kurallarının doğrudan fonksiyonlara eşlenmesi nedeniyle anlaşılması ve uygulanması kolaydır.

Soyut Sözdizimi Ağacı (AST)

Parser, sadece kodu doğrulamakla kalmaz, aynı zamanda kodun hiyerarşik yapısını temsil eden bir AST üretir. AstNode sınıfı, bu ağacın her bir düğümünü temsil eder. Örneğin, x = 10 + 20 ifadesi için aşağıdaki gibi bir alt ağaç oluşturulur:

- assignment: '='
  - identifier: 'x'
  - binary_op: '+'
    - number: '10'
    - number: '20'

Bu AST, "Show Syntax Tree (AST)" butonuyla arayüzde görselleştirilir.

Anlamsal Kontroller ve Kapsam Yönetimi

Parser, basit anlamsal kontroller de yapar.

Kapsam Yığını (kapsam_yigini): Bir liste (list) veri yapısı, kapsamları bir yığın gibi yönetmek için kullanılır. kapsama_gir (yığına yeni bir set ekler) ve kapsamdan_cik (yığından bir set çıkarır) metotları ile yönetilir.

Tanımlılık Kontrolü: Bir IDENT token'ı bir ifadede kullanıldığında, tanimli_mi metodu çağrılır. Bu metot, yığını mevcut kapsamdan globale doğru (reversed) tarayarak ismin tanımlı olup olmadığını kontrol eder. Eğer isim bulunamazsa, bir AnlamsalHata fırlatılır.

Dilbilgisi (Grammar) Kuralları

Parser'ın uyguladığı basitleştirilmiş gramer (BNF benzeri notasyonla):

program    ::= ifade*
ifade      ::= atama | if_ifadesi | def_ifadesi | return_ifadesi | hesaplama
blok       ::= ifade
if_ifadesi ::= 'if' hesaplama ':' blok ['else' ':' blok]
def_ifadesi::= 'def' IDENT '(' [param_list] ')' ':' blok
atama      ::= IDENT '=' hesaplama
hesaplama  ::= karsilastirma ( ('+'|'-') karsilastirma )*
carpan     ::= NUMBER | STRING | IDENT | fonksiyon_cagrisi | '(' hesaplama ')'

5. Grafiksel Kullanıcı Arayüzü (GUI)
Bileşenler ve SyntaxHighlighter Sınıfı

Arayüz, PyQt5 ile oluşturulmuş ve SyntaxHighlighter sınıfı tarafından yönetilmektedir. Ana bileşenler şunlardır:

QTextEdit: Kod giriş alanı.

QTreeWidget: Sözcüksel veya sözdizimsel ağacı göstermek için kullanılır.

QPushButton: Kullanıcı etkileşimleri için butonlar.

QLabel: Hata mesajlarını göstermek için.

QSplitter: Panellerin boyutunu ayarlanabilir kılar.

Sözdizimi Vurgulama Mantığı

Bu proje, proje gereksinimlerine uygun olarak hazır bir sözdizimi vurgulama kütüphanesi kullanmaz. Vurgulama işlemi tokenlari_vurgula metodu içinde manuel olarak yapılır:

Metin editöründeki tüm mevcut formatlama tum_formatlamayi_temizle ile sıfırlanır.

Lexer'dan gelen tokenlar listesi üzerinde bir döngü başlatılır.

Her bir token için, QTextCursor kullanılarak metindeki konumu seçilir.

Token'ın türüne göre önceden belirlenmiş bir renk ve stil içeren QTextCharFormat nesnesi oluşturulur.

cursor.setCharFormat() metodu ile seçilen metne format uygulanır.

Gerçek Zamanlı Güncelleme Mekanizması

Kullanıcı deneyimini ve performansı iyileştirmek için "debouncing" tekniği uygulanmıştır. Metin her değiştiğinde analiz hemen başlamaz. Bunun yerine, textChanged sinyali bir QTimer'ı 300 milisaniyeye ayarlar. Eğer bu süre içinde yeni bir değişiklik olmazsa, zamanlayıcı vurgula_ve_ayristir metodunu tetikler. Bu, her tuş vuruşunda analiz yapılmasını engelleyerek uygulamayı akıcı tutar.

6. Hata Yönetimi

Uygulama, üç farklı hata türünü yönetmek için özel istisna sınıfları kullanır. vurgula_ve_ayristir içindeki ana try...except bloğu bu hataları yakalar ve türüne göre kullanıcıya anlamlı bir mesaj gösterir:

SozcukselHata -> "Lexical Error: ..."

SozdizimselHata -> "Syntax Error: ..."

AnlamsalHata -> "Semantic Error: ..."

Diğer tüm beklenmedik hatalar -> "Unexpected Error: ..."
