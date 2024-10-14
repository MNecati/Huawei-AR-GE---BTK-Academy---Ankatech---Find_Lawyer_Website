
from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import pickle
import numpy as np
from sklearn.preprocessing import LabelEncoder
from flask_cors import CORS
import hashlib

lbe = LabelEncoder()
app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Flash mesajları için gerekli


with open("trained_model.sav", "rb") as file:
    model = pickle.load(file)

    
from flask import jsonify



@app.route('/predict_case', methods=['POST'])
def predict_case():
    # Form verilerini al
    dava_turu = int(request.form['dava_turu'])
    delil_durumu = int(request.form['delil_durumu'])
    tanik_sayisi = int(request.form['tanik_sayisi'])
    delil_sayisi = int(request.form['delil_sayisi'])
    hukuki_dayanak = request.form['hukuki_dayanak']
    hukuki_temsil = request.form['hukuki_temsil']
    onceki_davalar = int(request.form['onceki_davalar'])
    dava_suresi = int(request.form['dava_suresi'])
    hukuki_menfaat = request.form['hukuki_menfaat']
    karmasiklik = request.form['karmaşıklık']
    yargi_durumu = request.form['yargi_durumu']
    uzlasma = request.form['uzlasma']
    uzman_gorus = request.form['uzman_gorus']


    # Verileri modele uygun formata çevir
    input_data = np.array([[dava_turu, delil_durumu, tanik_sayisi, delil_sayisi, hukuki_dayanak, hukuki_temsil, onceki_davalar, dava_suresi, hukuki_menfaat,  karmasiklik, yargi_durumu, uzlasma, uzman_gorus]])



    # Model ile tahmin yap
    prediction = model.predict(input_data)
    # JSON olarak yanıt ver
    result = {
        'prediction': 'Dava kazanılabilir' if prediction == 1 else 'Dava kaybedilebilir'
    }
    return jsonify(result)




# Database connection setup with error handling
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='101.44.34.253',  # EIP adresin
            user='root',
            password='ankatech!1',
            database='ankatech'
        )
        if connection.is_connected():
            print("Veritabanı bağlantısı başarılı, uygulama çalışıyor...")  # Başarılı bağlantı mesajı
            return connection
    except Error as e:
        print(f"Veritabanına bağlanırken hata oluştu: {e}")  # Hata durumunda terminale yazdır
        return None

@app.route('/')
def index():
    return render_template('index.html')  # Tarayıcıya HTML şablonu döndür
"""@app.route('/iletisim')
def iletisim():
    return render_template('iletisim.html') """

import hashlib

@app.route('/login', methods=['GET', 'POST'])  # POST metodunu ekledik
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['userType']

        # Şifreyi MD5 ile hashle
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        conn = get_db_connection()  # Veritabanı bağlantısını al
        if conn:
            cursor = conn.cursor()
            # Kullanıcı adı ve şifreyi doğrulama
            if user_type == 'avukat':
                cursor.execute("SELECT * FROM avukat WHERE username = %s AND password = %s", (username, hashed_password))
            else:
                cursor.execute("SELECT * FROM kullanici WHERE username = %s AND password = %s", (username, hashed_password))
                
            user = cursor.fetchone()  # Kullanıcıyı bul
            cursor.close()
            conn.close()  # Bağlantıyı kapat
            
            if user:  # Kullanıcı bulunduysa
                session['username'] = username 
                # Oturumu başlat
                if user_type == 'avukat':
                    session['sicil_no'] = user[4]  # Sicil numarasını session'a ekle (sütun indeksi 4 olarak varsayıyoruz, ihtiyaca göre ayarlayın)
                flash('Giriş başarılı!', 'success')
                return redirect(url_for('index'))  # Anasayfaya yönlendir
            else:
                flash('Kullanıcı adı veya şifre hatalı.', 'danger')  # Hata mesajı
    return render_template('login.html')  # Giriş formunu döndür

@app.route('/register', methods=['GET', 'POST'])  # POST metodu ekledik
def register():
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        username = request.form['registerUsername']
        password = request.form['registerPassword']
        user_type = request.form['registerUserType']
        
        # Şifreyi MD5 ile hashle
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        conn = get_db_connection()  # Veritabanı bağlantısını al
        if conn:
            cursor = conn.cursor()
            if user_type == 'avukat':
                sicil_no = request.form['sicilNo']
                department = request.form['department']
                
                # Avukat kaydı
                cursor.execute(""" 
                    INSERT INTO avukat (first_name, last_name, username, password, sicil_no, department) 
                    VALUES (%s, %s, %s, %s, %s, %s) 
                """, (first_name, last_name, username, hashed_password, sicil_no, department))
            else:
                # Normal kullanıcı kaydı
                cursor.execute(""" 
                    INSERT INTO kullanici (first_name, last_name, username, password) 
                    VALUES (%s, %s, %s, %s) 
                """, (first_name, last_name, username, hashed_password))
            
            conn.commit()  # Değişiklikleri kaydet
            cursor.close()
            conn.close()  # Bağlantıyı kapat
            
            flash('Kayıt başarılı! Giriş yapmayı deneyin.', 'success')
            return redirect(url_for('login'))  # Başarılı kayıt sonrası giriş sayfasına yönlendir
        else:
            flash('Veritabanına bağlanılamadı.', 'danger')  # Veritabanı bağlantı hatası
        
    return render_template('register.html')  # GET isteği için kayıt formunu döndür


@app.route('/logout')
def logout():
    session.pop('username', None)  # Oturumdan kullanıcı adını kaldır
    session.pop('sicil_no', None)  # Sicil numarasını session'dan kaldır
    flash('Çıkış başarılı!', 'success')  # Başarı mesajı
    return redirect(url_for('index'))  # Anasayfaya yönlendir

# Diğer sayfa rotaları
@app.route('/hakkımızda')
def hakkımızda():
    return render_template('hakkımızda.html')

@app.route('/sss')
def sss():
    return render_template('sss.html')

@app.route('/yapayzeka')
def yapayzeka():
    return render_template('yapayzeka.html')

@app.route('/avukat')
def avukat():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # İlan tablosundaki tüm ilanları seçiyoruz, açıklamayı da ekliyoruz
        cursor.execute("SELECT isim_soyisim, uzmanlik, email, telefon_numarasi, deneyim_yil, buro_konum, puan, aciklama FROM ilan")
        ilanlar = cursor.fetchall()  # Verileri çekiyoruz
        
        cursor.close()
        conn.close()
        
        return render_template('avukat.html', ilanlar=ilanlar)  # Verileri template'e gönderiyoruz
    else:
        flash('Veritabanına bağlanılamadı.', 'danger')
        return render_template('avukat.html', ilanlar=[])  # Hata durumunda boş liste gönderiyoruz


@app.route('/ilan', methods=['GET', 'POST'])
def ilan():
    mesaj = None  # Mesajı tutmak için bir değişken oluştur
    if request.method == 'POST':
        isim_soyisim = request.form['isimSoyisim']
        uzmanlik = request.form['uzmanlik']
        email = request.form['email']
        telefon = request.form['telefon']
        deneyim = request.form['deneyim']
        konum = request.form['konum']
        aciklama = request.form['aciklama']  # Açıklama alıyoruz
        puan = 0  # Puanı otomatik olarak 0 olarak ayarlıyoruz

        conn = get_db_connection()  # Veritabanı bağlantısı al
        if conn:
            cursor = conn.cursor()
            # İlan verisini veritabanına ekle
            cursor.execute(""" 
                INSERT INTO ilan (isim_soyisim, uzmanlik, email, telefon_numarasi, deneyim_yil, buro_konum, puan, aciklama)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (isim_soyisim, uzmanlik, email, telefon, deneyim, konum, puan, aciklama))  # Açıklamayı ekliyoruz

            conn.commit()  # Değişiklikleri kaydet
            cursor.close()
            conn.close()  # Bağlantıyı kapat
            
            mesaj = 'Tebrikler, yanıtınız kaydedildi!'  # Başarılı mesajı
        else:
            mesaj = 'Veritabanına bağlanılamadı.'  # Hata mesajı

    return render_template('ilan.html', mesaj=mesaj)  # Mesajı template'e gönder

#iletisime geç kısmı
def contact():
    if request.method == 'POST':
        email = request.form['email']
        # E-posta ile ilgili işlemleri burada yapın (örneğin, veritabanına kaydetme veya e-posta gönderme)
        return redirect(url_for('thank_you'))  # Teşekkür sayfasına yönlendirme
    return render_template('contact.html')

@app.route('/thank-you')
def thank_you():
    return "Teşekkürler! Mesajınız alınmıştır."
@app.route('/iletisim', methods=['GET', 'POST'])
def iletisim():
    eposta = request.args.get('email', '')  # URL'den e-posta değerini al
    ilan_id = request.args.get('ilan_id', '')
    if request.method == 'POST':
        # Burada e-posta gönderme işlemleri yapılabilir
        pass
    return render_template('iletisim.html', eposta=eposta, ilan_id=ilan_id)
#asistan
@app.route('/asistan')
def asistan():
    return render_template('asistan.html')
###E-Mail servisi
@app.route('/send_email', methods=['POST'])
def send_email():
    ad = request.form['ad']
    soyad = request.form['soyad']
    adres = request.form['adres']
    kullanici_email = request.form['kullanici_e-posta']
    avukat_email = request.form['email']
    randevu_tarihi = request.form['randevu_tarihi']
    mesaj = request.form['mesaj']

    # Yandex SMTP ayarları
    yandex_email = 'huaweiargekodlama@yandex.com'  # Yandex e-posta adresiniz
    yandex_password = 'vxnzekvivqjrisne'  # Yandex uygulama şifreniz

    # E-posta içeriği oluşturma
    msg = MIMEMultipart()
    msg['From'] = yandex_email
    msg['To'] = avukat_email
    msg['Subject'] = 'Avukatınız ile iletişime geçin'  # Dinamik başlık

    body = f'''
    <p><strong>Ad:</strong> {ad}</p>
    <p><strong>Soyad:</strong> {soyad}</p>
    <p><strong>Adres:</strong> {adres}</p>
    <p><strong>Kullanıcı E-posta:</strong> {kullanici_email}</p>
    <p><strong>Randevu Tarihi:</strong> {randevu_tarihi}</p>
    <p><strong>Mesaj:</strong> {mesaj}</p>
    '''
    msg.attach(MIMEText(body, 'html'))

    try:
        # Yandex SMTP sunucusuna bağlan
        server = smtplib.SMTP_SSL('smtp.yandex.com', 465)  # SSL kullanarak bağlantı
        server.login(yandex_email, yandex_password)  # Giriş yap
        server.send_message(msg)  # E-postayı gönder
        server.quit()  # Bağlantıyı kapat
        return 'E-posta başarıyla gönderildi!', 200
    except Exception as e:
        print(f"Hata: {e}")
        return f"E-posta gönderilemedi! Hata: {e}", 500
#avukat sorgu
@app.route('/avukat_sorgu', methods=['GET'])
def avukat_sorgu():
    avukat_turu = request.args.get('avukat')  # Kullanıcının girdiği avukat türünü al

    # MySQL bağlantısı
    conn = mysql.connector.connect(
            host='101.44.34.253',  # EIP adresin
            user='root',
            password='ankatech!1',
            database='ankatech'
    )
    cursor = conn.cursor()

    # SQL sorgusu
    query = "SELECT isim_soyisim, uzmanlik, email, telefon_numarasi, deneyim_yil, buro_konum, puan, aciklama FROM ilan WHERE uzmanlik LIKE %s"
    cursor.execute(query, ('%' + avukat_turu + '%',))  # Anahtar kelime ile filtreleme

    # Sonuçları al
    ilanlar = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('avukat_sorgu.html', ilanlar=ilanlar)  # Sonuçları HTML ş

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

