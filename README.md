# Python Tabanlı Gerçek Zamanlı Sözdizimi Vurgulayıcı ve Ayrıştırıcı

Bu proje, Python ve PyQt5 kullanılarak geliştirilmiş, Python benzeri basit bir dil için gerçek zamanlı analiz yetenekleri sunan bir masaüstü uygulamasıdır. Kod yazılırken anlık olarak sözdizimi vurgulaması, hata tespiti ve yapısal analiz yapar.


## ✨ Temel Özellikler

-   **Gerçek Zamanlı Sözdizimi Vurgulama:** Anahtar kelimeler, sayılar, metinler, yorumlar ve operatörler gibi 8 farklı token türünü anlık olarak renklendirir.
-   **Anlık Hata Tespiti:** Kod yazılırken üç farklı seviyede hata tespiti yapar:
    -   **Sözcüksel Hatalar:** Tanımsız semboller (`@`, `?` vb.).
    -   **Sözdizimsel Hatalar:** Dilbilgisine uymayan yapılar (eksik parantez, hatalı ifade vb.).
    -   **Anlamsal Hatalar:** Tanımlanmamış değişken veya fonksiyon kullanımı.
-   **Çift Ağaç Görünümü:**
    -   **Lexical Tree:** Kodun nasıl token'lara ayrıldığını gösterir.
    -   **Syntax Tree (AST):** Kodun yapısal ve hiyerarşik ağacını (Soyut Sözdizimi Ağacı) görselleştirir.
-   **Kapsam Yönetimi (Scope):** Global, fonksiyon ve blok kapsamlarını destekler.
-   **Demo Butonu:** Uygulamanın yeteneklerini sergilemek için tek tıkla örnek kod yükler.

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
-   Python 3 (önerilen sürüm 3.6 veya üzeri)
-   PyQt5

### Adımlar
1.  **Projeyi Klonlayın veya İndirin:**
    ```bash
    git clone https://github.com/kullanici-adiniz/proje-repo-adi.git
    cd proje-repo-adi
    ```

2.  **Gerekli Kütüphaneyi Yükleyin:**
    Proje sadece PyQt5 kütüphanesine ihtiyaç duymaktadır.
    ```bash
    pip install PyQt5
    ```

3.  **Uygulamayı Başlatın:**
    Projenin ana Python dosyasını çalıştırın.
    ```bash
    python main.py 
    ```

## 🛠️ Kullanılan Teknolojiler

-   **Programlama Dili:** Python 3
-   **GUI Kütüphanesi:** PyQt5
-   **Temel Modüller:** `re` (Düzenli İfadeler için), `sys`

## 📄 Dokümantasyon

Projenin teknik detayları, mimari kararları ve bileşenlerin çalışma prensipleri hakkında daha fazla bilgi için [DOCUMENTATION.md](DOCUMENTATION.md) dosyasına göz atın.

## 📹 Demo Video & 📝 Makale

Projenin çalışma prensiplerini ve özelliklerini gösteren demo videosu ve teknik makaleye aşağıdaki linklerden ulaşabilirsiniz:

-   **[Demo Video Linki]**
-   **[Teknik Makale Linki]**
