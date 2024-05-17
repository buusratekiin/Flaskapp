from flask import Flask, render_template, request, redirect, url_for, session,flash,jsonify
import sqlite3
#from urllib import request
from flask_saml2.sp import ServiceProvider
from flask_saml2.utils import certificate_from_file, private_key_from_file

#app = Flask(__name__)
class KeycloakServiceProvider(ServiceProvider):
    def get_logout_return_url(self):
        return url_for('index', _external=True)

    def get_default_login_return_url(self):
        return url_for('index', _external=True)

sp = KeycloakServiceProvider()
app = Flask(__name__)
app.debug = True
app.secret_key = 'not a secret'
app.config['SERVER_NAME'] = '10.100.40.107:5002'
app.config['SAML2_SP'] = {
      'certificate': certificate_from_file('idp_cert.pem'),
    'private_key': private_key_from_file('sp_key.pem'),
}
# Kimlik denetmeleme sağlayıcı
app.config['SAML2_IDENTITY_PROVIDERS'] = [
    {
        'CLASS': 'flask_saml2.sp.idphandler.IdPHandler',
        'OPTIONS': {
            'display_name': 'KeyCloak',
            'entity_id': 'http://10.100.40.107:8080/auth/realms/test',
            'sso_url': 'http://10.100.40.107:8080/auth/realms/test/protocol/saml',
            'slo_url': 'http://10.100.40.107:8080/auth/realms/test/protocol/saml',
            'certificate': certificate_from_file('idp_cert.pem')
        },
    },
]

# Veritabanı dosya yolu
db_filename = 'vm.db'
app.secret_key = 'buraya_gizli'
# Tabloları oluşturma fonksiyonu
def create_tables():
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    
    # User tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY,
            name TEXT,
            surname TEXT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # VmTable tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS VmTable (
            id INTEGER PRIMARY KEY,
            alan TEXT NOT NULL,
            tur TEXT NOT NULL,
            vm_name TEXT NOT NULL,
            management_ip TEXT NOT NULL,
            management_user TEXT NOT NULL,
            management_password TEXT NOT NULL,
            os_ip TEXT NOT NULL,
            os_user TEXT NOT NULL,
            os_password TEXT NOT NULL,
            description TEXT
        )
    ''')


    conn.commit()
    conn.close()
    print("Tablolar başarıyla oluşturuldu.")

@app.route('/update_vm/<int:id>', methods=['POST'])
def update_vm(id):
    data = request.get_json()
    if not data:
        return 'No data provided', 400

    adi = data.get('adi')
    alan=data.get('alan')
    tur=data.get('tur')
    mgmtIP = data.get('mgmtIP')
    mgmtUser = data.get('mgmtUser')
    mgmtPass = data.get('mgmtPass')
    osIP = data.get('osIP')
    osUser = data.get('osUser')
    osPass = data.get('osPass')
    aciklama = data.get('aciklama')

    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE VmTable
        SET alan=?,tur=?,vm_name = ?, management_ip = ?, management_user = ?, management_password = ?, os_ip = ?, os_user = ?, os_password = ?, description=?
        WHERE id = ?
    ''', (alan, tur, adi, mgmtIP, mgmtUser, mgmtPass, osIP, osUser, osPass, aciklama,id))
    conn.commit()
    conn.close()

    return render_template('tables.html')

# Yeni bir VmTable kaydı ekleme fonksiyonu
def add_vm(alan, tur, vm_name, management_ip, management_user, management_password, os_ip, os_user, os_password, description):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO VmTable (alan, tur, vm_name, management_ip, management_user, management_password, os_ip, os_user, os_password, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (alan, tur, vm_name, management_ip, management_user, management_password, os_ip, os_user, os_password, description))
    conn.commit()
    conn.close()
    print("VmTable kaydı başarıyla eklendi.")
    
@app.route('/get_vm/<int:id>', methods=['GET'])
def get_vm(id):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM VmTable WHERE id = ?', (id,))
    vm_record = cursor.fetchone()
    conn.close()
    
    if vm_record:
        return jsonify({
            'id': vm_record[0],
            'alan':vm_record[1],
            'tur': vm_record[2],  # Tür
            'adi': vm_record[3],  # Alan
            
            'mgmtIP': vm_record[4],  # Mgmt IP
            'mgmtUser': vm_record[5],  # Mgmt User
            'mgmtPass': vm_record[6],  # Mgmt Password
            'osIP': vm_record[7],  # OS IP
            'osUser': vm_record[8],  # OS User
            'osPass': vm_record[9],  # OS Password
            'aciklama': vm_record[10],  # Açıklama
        })
    else:
        return jsonify({'error': 'Record not found'}), 404
    
@app.route('/delete_vm/<int:id>', methods=['POST'])
def delete_vm(id):
    conn=sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM VmTable WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_tables'))


def add_user(name, surname, username, password):
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO User (name, surname, username, password)
        VALUES (?, ?, ?, ?)
    ''', (name, surname, username, password))
    conn.commit()
    conn.close()
    print("User added successfully.")

def login(username,password):
    conn= sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchall()
    conn.close()
    return user

@app.route('/login', methods=['POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = login(username, password)
        if user:
            # Kullanıcı doğru ise, giriş yap ve yönlendir
            session['username'] = username 
            return redirect(url_for('view_tables'))
        else:
            # Kullanıcı bulunamadıysa, hata göster
            return render_template('login.html', error=True)

    # GET isteği geldiğinde login sayfasını göster
    return render_template('login.html', error=False)
# VmTable kayıtlarını listeleme fonksiyonu
def list_vmtables():
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM VmTable')
    vmtables = cursor.fetchall()
    conn.close()
    return vmtables

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/tablesadd', methods=['GET', 'POST'])
def add_table():
     if 'username' in session:
        if request.method == 'POST':
            if request.form['Alan']=="Diger1":
                alan=request.form["otheralan"]
            else:
                alan = request.form['Alan']
            if request.form['Tur']=="Diger2":
               tur = request.form['othertur']
            else:        
               tur = request.form['Tur']
            vm_name = request.form['VmName']
            management_ip = request.form['ManagemendIP']
            management_user = request.form['ManagemendUser']
            management_password = request.form['ManagemendPass']
            os_ip = request.form['OsIp']
            os_user = request.form['OsUser']
            os_password = request.form['Ospass']
            description = request.form['Aciklama']
            
           

            add_vm(alan, tur, vm_name, management_ip, management_user, management_password, os_ip, os_user, os_password, description)
            flash("Kayıt başarıyla oluşturuldu.", "success")
            return redirect(url_for('add_table'))
        
        return render_template('tablesadd.html')
     #ekledim
     elif sp.is_user_logged_in():
        auth_data = sp.get_auth_data_in_session()
        if request.method == 'POST':
            vm_name = request.form['VmName']
            vm_ip = request.form['VmIp']
            description = request.form['Aciklama']
            ipmi = request.form['IpMI']
            user_id = request.form['Kullanici']
            vm_password = request.form['Sifre']
            

            add_vm(vm_name, vm_ip, description, ipmi, user_id, vm_password)
            
            return redirect(url_for('add_table'))

        return render_template('tablesadd.html')
        
     else:
        return redirect(url_for('index'))  # Giriş yapmamış kullanıcıyı giriş sayfasına yönlendir


@app.route('/logout')
def logout():
    session.pop('username', None)  # Oturumdan kullanıcı adını kaldır
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        username = request.form['username']
        password = request.form['password']

        # Add user to the database
        add_user(name, surname, username, password)

        # Redirect to login page
        return redirect(url_for('register'))

    return render_template('register.html')
@app.route('/tables')
def view_tables():
    if 'username' in session:
        vmtables = list_vmtables()
        
        return render_template('tables.html', vmtables=vmtables)
    #ekledim
    elif sp.is_user_logged_in():
        auth_data = sp.get_auth_data_in_session()
        vmtables = list_vmtables()
        return render_template('tables.html', vmtables=vmtables)

    else:
        return redirect(url_for('index'))  # Giriş yapmamış kullanıcıyı giriş sayfasına yönlendir

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


    

if __name__ == '__main__':
    create_tables()  # Tabloları oluştur
    app.run(debug=True,host="0.0.0.0")