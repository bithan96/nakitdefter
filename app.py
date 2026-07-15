from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
import sqlite3, re, os, random, time
from dotenv import load_dotenv
load_dotenv()
from database import init_db, get_db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests
from datetime import datetime, date

init_db()

app = Flask(__name__)
app.secret_key = "nakitdefter_secret"

# Email (Brevo) 
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")

def send_email(to_email, code):
    with app.app_context():
        html = render_template("otp_email.html", name=to_email, otp=code)
    try:
        requests.post("https://api.brevo.com/v3/smtp/email",
            headers={"accept":"application/json","api-key":BREVO_API_KEY,"content-type":"application/json"},
            json={"sender":{"name":"NakitDefter","email":SENDER_EMAIL},
                  "to":[{"email":to_email}],
                  "subject":"NAKITDEFTER Doğrulama","htmlContent":html})
    except Exception as e:
        print("EMAIL ERROR:", e)
    print("OTP:", code)

#  Helpers 
UPLOAD_FOLDER = os.path.join("static", "profile_pics")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT = {"png","jpg","jpeg","gif"}

def allowed_file(f): return "." in f and f.rsplit(".",1)[1].lower() in ALLOWED_EXT
def valid_password(p):
    return len(p) >= 4
def login_required():
    return not session.get("logged_in")

#Mock bank data 
MOCK_BANKS = {
    "Garanti BBVA": {
        "account_no": "TR33 0006 2001 2345 6789 0123 45",
        "balance": 18750.00,
        "transactions": [
            ("Market - Garanti","expense",320.50),
            ("Maaş - Garanti","income",15000.00),
            ("Fatura - Garanti","expense",245.00),
            ("Restoran - Garanti","expense",180.00),
            ("Kira Geliri - Garanti","income",3500.00),
        ]
    },
    "İş Bankası": {
        "account_no": "TR26 0006 4000 0011 2233 4455 66",
        "balance": 12500.00,
        "transactions": [
            ("Alışveriş - İş Bankası","expense",450.00),
            ("Maaş - İş Bankası","income",12000.00),
            ("Elektrik - İş Bankası","expense",310.00),
            ("Yakıt - İş Bankası","expense",600.00),
        ]
    },
    "Yapı Kredi": {
        "account_no": "TR92 0006 7010 0000 0055 5555 55",
        "balance": 9200.00,
        "transactions": [
            ("Market - Yapı Kredi","expense",275.00),
            ("Freelance Gelir","income",8000.00),
            ("Su Faturası","expense",95.00),
        ]
    },
    "Ziraat Bankası": {
        "account_no": "TR12 0001 0017 4538 8016 0000 01",
        "balance": 22000.00,
        "transactions": [
            ("Maaş - Ziraat","income",20000.00),
            ("Alışveriş - Ziraat","expense",750.00),
            ("Sigorta - Ziraat","expense",520.00),
            ("Kira - Ziraat","expense",5000.00),
        ]
    },
    "Akbank": {
        "account_no": "TR48 0004 6004 6888 8000 1111 11",
        "balance": 7800.00,
        "transactions": [
            ("Maaş - Akbank","income",7500.00),
            ("Market - Akbank","expense",390.00),
            ("İnternet - Akbank","expense",199.00),
        ]
    },
}

#Onboarding / Index 
 
@app.route("/")
def index(): return redirect(url_for("onboarding2"))

@app.route("/onboarding2")
def onboarding2(): return render_template("onboarding2.html")

#Signup 
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email    = request.form["email"]
        password = request.form["password"]
        if not valid_password(password):
         flash("Şifre en az 4 karakter olmalıdır","error")
         return render_template("signup.html") 
        
    

        db = get_db(); c = db.cursor()
        if c.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone():
            db.close(); flash("Bu email zaten kayıtlı.","error"); return render_template("signup.html")
        if c.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone():
            db.close(); flash("Bu kullanıcı adı alınmış.","error"); return render_template("signup.html")
        code   = str(random.randint(100000,999999))
        expiry = int(time.time()) + 300
        c.execute("INSERT INTO users(username,email,password,is_verified,verification_code,code_expiry) VALUES(?,?,?,?,?,?)",
                  (username,email,generate_password_hash(password),0,code,expiry))
        db.commit(); db.close()
        send_email(email, code)
        session["verify_email"] = email
        flash("Doğrulama kodu gönderildi","success")
        return redirect(url_for("verify_signup"))
    return render_template("signup.html")

#Verify signup 
@app.route("/verify_signup", methods=["GET","POST"])
def verify_signup():
    if request.method == "POST":
        code  = request.form["code"].strip()
        email = session.get("verify_email")
        if not email: flash("Geçersiz işlem","error"); return redirect(url_for("signup"))
        db = get_db(); c = db.cursor()
        row = c.execute("SELECT id,username,email,password,profile_pic,verification_code,code_expiry FROM users WHERE email=?",(email,)).fetchone()
        if not row: db.close(); flash("Kullanıcı bulunamadı","error"); return redirect(url_for("signup"))
        if row["code_expiry"] and int(time.time()) > row["code_expiry"]:
            db.close(); flash("Kod süresi doldu","error"); return redirect(url_for("verify_signup"))
        if code == row["verification_code"]:
            c.execute("UPDATE users SET is_verified=1,verification_code=NULL,code_expiry=NULL WHERE email=?",(email,))
            db.commit(); db.close()
            session.pop("verify_email",None)
            session.update({"logged_in":True,"user_id":row["id"],"username":row["username"],
                            "email":row["email"],"profile_pic":row["profile_pic"]})
            flash("Doğrulama başarılı, hoş geldiniz!","success"); return redirect(url_for("dashboard"))
        db.close(); flash("Kod yanlış","error")
    return render_template("verify.html")

#Verify reset 
@app.route("/verify_reset", methods=["GET","POST"])
def verify_reset():
    if request.method == "POST":
        code  = request.form["code"]
        email = session.get("reset_email")
        if not email: flash("Geçersiz işlem","error"); return redirect(url_for("forgot_password"))
        db = get_db(); c = db.cursor()
        row = c.execute("SELECT reset_code,code_expiry FROM users WHERE email=?",(email,)).fetchone()
        if not row: db.close(); flash("Kullanıcı bulunamadı","error"); return redirect(url_for("forgot_password"))
        if row["code_expiry"] and int(time.time()) > row["code_expiry"]:
            db.close(); flash("Kod süresi doldu","error"); return redirect(url_for("verify_reset"))
        if code == row["reset_code"]:
            db.close(); session["reset_verified"] = True; return redirect(url_for("change_password"))
        db.close(); flash("Kod yanlış","error")
    return render_template("verify.html")

@app.route("/verify")
def verify(): return redirect(url_for("verify_signup"))

#Login / Logout 
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db(); c = db.cursor()
        user = c.execute("SELECT * FROM users WHERE username=? OR email=?",(username,username)).fetchone()
        if not user: db.close(); flash("Kullanıcı kayıtlı değil.","error"); return render_template("login.html")
        if not check_password_hash(user["password"], password):
            db.close(); flash("Şifre yanlış.","error"); return render_template("login.html")
        if user["is_verified"] == 0:
            session["verify_email"] = user["email"]
            flash("Email doğrulanmamış","error"); return redirect(url_for("verify_signup"))
        session.update({"logged_in":True,"user_id":user["id"],"username":user["username"],
                        "email":user["email"],"profile_pic":user["profile_pic"]})
        db.close(); return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

#Forgot / Change password 
@app.route("/forgot_password", methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        db = get_db(); c = db.cursor()
        if not c.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone():
            db.close(); flash("Bu email kayıtlı değil","error"); return redirect(url_for("forgot_password"))
        code   = str(random.randint(100000,999999))
        expiry = int(time.time()) + 300
        c.execute("UPDATE users SET reset_code=?,code_expiry=? WHERE email=?",(code,expiry,email))
        db.commit(); db.close()
        send_email(email, code)
        session["reset_email"] = email
        flash("Kod gönderildi","success"); return redirect(url_for("verify_reset"))
    return render_template("forgot_password.html")

@app.route("/change_password", methods=["GET","POST"])
def change_password():
    if request.method == "POST":
        new_pw = request.form["new_password"]
        db = get_db(); c = db.cursor()
        if session.get("logged_in"):
            user = c.execute("SELECT password FROM users WHERE id=?",(session["user_id"],)).fetchone()
            if not check_password_hash(user["password"], request.form.get("old_password","")):
                db.close(); flash("Mevcut şifre yanlış","error"); return redirect(url_for("change_password"))
            c.execute("UPDATE users SET password=? WHERE id=?",(generate_password_hash(new_pw),session["user_id"]))
        else:
            if not session.get("reset_verified"): flash("Önce doğrulama yapın","error"); return redirect(url_for("forgot_password"))
            email = session.get("reset_email")
            c.execute("UPDATE users SET password=?,reset_code=NULL,code_expiry=NULL WHERE email=?",
                      (generate_password_hash(new_pw),email))
            session.pop("reset_email",None); session.pop("reset_verified",None)
        db.commit(); db.close()
        flash("Şifre güncellendi","success"); return redirect(url_for("login"))
    return render_template("change_password.html")

#Delete account 
@app.route("/delete_account")
def delete_account():
    if login_required(): return redirect(url_for("login"))
    db = get_db(); c = db.cursor()
    c.execute("DELETE FROM transactions WHERE user_id=?",(session["user_id"],))
    c.execute("DELETE FROM goals WHERE user_id=?",(session["user_id"],))
    c.execute("DELETE FROM linked_accounts WHERE user_id=?",(session["user_id"],))
    c.execute("DELETE FROM users WHERE id=?",(session["user_id"],))
    db.commit(); db.close(); session.clear()
    flash("Hesabınız silindi","success"); return redirect(url_for("signup"))

#Upload photo 
@app.route("/upload_photo", methods=["GET","POST"])
def upload_photo():
    if login_required(): return redirect(url_for("login"))
    if request.method == "POST":
        file = request.files.get("photo")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            db = get_db(); c = db.cursor()
            c.execute("UPDATE users SET profile_pic=? WHERE id=?",(filename,session["user_id"]))
            db.commit(); db.close()
            session["profile_pic"] = filename
            flash("Profil fotoğrafı güncellendi","success")
        else:
            flash("Geçersiz dosya formatı","error")
        return redirect(url_for("dashboard"))
    return render_template("upload_photo.html")

#Resend code 
@app.route("/resend_code", methods=["POST"])
def resend_code():
    email = session.get("verify_email") or session.get("reset_email")
    if not email: return redirect(url_for("login"))
    code   = str(random.randint(100000,999999))
    expiry = int(time.time()) + 300
    db = get_db(); c = db.cursor()
    if session.get("verify_email"):
        c.execute("UPDATE users SET verification_code=?,code_expiry=? WHERE email=?",(code,expiry,email))
        page = "verify_signup"
    else:
        c.execute("UPDATE users SET reset_code=?,code_expiry=? WHERE email=?",(code,expiry,email))
        page = "verify_reset"
    db.commit(); db.close()
    send_email(email, code)
    flash("Kod tekrar gönderildi","success"); return redirect(url_for(page))

#Dashboard 
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if login_required(): return redirect(url_for("login"))
    db = get_db(); c = db.cursor()
    uid = session["user_id"]

    # Add new transaction
    if request.method == "POST":
        title  = request.form["title"].strip()
        amount = float(request.form["amount"])
        type_  = request.form["type"]
        if not title: flash("Açıklama boş olamaz","error"); return redirect(url_for("dashboard"))
        if amount <= 0: flash("Tutar pozitif olmalı","error"); return redirect(url_for("dashboard"))
        c.execute("INSERT INTO transactions(user_id,title,amount,type) VALUES(?,?,?,?)",(uid,title,amount,type_))
        db.commit(); return redirect(url_for("dashboard"))

    # Summary totals
    transactions = c.execute("SELECT id,title,amount,type,created_at FROM transactions WHERE user_id=? ORDER BY id DESC",(uid,)).fetchall()
    income  = c.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND user_id=?",(uid,)).fetchone()[0] or 0
    expense = c.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND user_id=?",(uid,)).fetchone()[0] or 0
    savings = income - expense

    # Goal data
    goal_row = c.execute("SELECT * FROM goals WHERE user_id=? ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
    goal_name=goal=total_months=monthly_target=goal_pct=cumulative_saved=0
    goal_start_date=goal_end_date=None
    months_data=saved_data=target_data=[]

    if goal_row:
        goal_name  = goal_row["goal_name"] or "Hedefim"
        goal       = goal_row["target_amount"] or 0
        start      = datetime.strptime(goal_row["start_date"][:10], "%Y-%m-%d")
        end        = datetime.strptime(goal_row["end_date"][:10],   "%Y-%m-%d")
        goal_start_date = goal_row["start_date"][:10]
        goal_end_date   = goal_row["end_date"][:10]
        total_months    = max(1,(end.year-start.year)*12+(end.month-start.month))
        monthly_target  = goal/total_months
        today           = datetime.today()
        months_data=[];saved_data=[];target_data=[]
        cumulative_saved = 0

        for i in range(total_months):
            yr  = start.year  + (start.month-1+i)//12
            mon = (start.month-1+i)%12+1
            lbl = f"{yr}-{mon:02d}"
            if date(yr,mon,1) > date(today.year,today.month,1):
                saved_data.append(None)
            else:
                row = c.execute("""
                    SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END)-
                           SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as net
                    FROM transactions WHERE user_id=?
                    AND strftime('%Y-%m',created_at)=? AND date(created_at)>=?
                """,(uid,lbl,goal_start_date)).fetchone()
                net = row["net"] if row and row["net"] else 0
                saved_data.append(round(max(0,net),2))
                cumulative_saved += net
            months_data.append(lbl)
            target_data.append(round(monthly_target,2))

        cumulative_saved = max(0, cumulative_saved)
        goal_pct = max(0, min(100, round(cumulative_saved/goal*100,1) if goal else 0))

    # Linked banks for dashboard widget
    linked = c.execute("SELECT bank_name,account_no,balance FROM linked_accounts WHERE user_id=?",(uid,)).fetchall()
    db.close()

    return render_template("dashboard.html",
        income=income, expense=expense, savings=savings, transactions=transactions,
        goal_name=goal_name, goal=goal, total_months=total_months,
        monthly_target=monthly_target, goal_pct=goal_pct,
        cumulative_saved=round(cumulative_saved,2),
        goal_start_date=goal_start_date, goal_end_date=goal_end_date,
        months_data=months_data, saved_data=saved_data, target_data=target_data,
        linked_banks=linked)

#Delete transaction 
@app.route("/delete/<int:tx_id>", methods=["POST"])
def delete(tx_id):
    if login_required(): return redirect(url_for("login"))
    db = get_db(); c = db.cursor()
    c.execute("DELETE FROM transactions WHERE id=? AND user_id=?",(tx_id,session["user_id"]))
    db.commit(); db.close(); return redirect(url_for("dashboard"))

#Set goal 
@app.route("/set_goal", methods=["POST"])
def set_goal():
    if login_required(): return redirect(url_for("login"))
    uid        = session["user_id"]
    goal_name  = request.form.get("goal_name","Hedefim").strip() or "Hedefim"
    target     = float(request.form["target"])
    start_date = request.form["start_date"]
    end_date   = request.form["end_date"]
    db = get_db(); c = db.cursor()
    c.execute("DELETE FROM goals WHERE user_id=?",(uid,))
    c.execute("INSERT INTO goals(user_id,goal_name,target_amount,start_date,end_date) VALUES(?,?,?,?,?)",
              (uid,goal_name,target,start_date,end_date))
    db.commit(); db.close()
    return redirect(url_for("dashboard"))

#Bank page 
@app.route("/bank")
def bank():
    if login_required(): return redirect(url_for("login"))
    db = get_db(); c = db.cursor()
    linked = c.execute("SELECT * FROM linked_accounts WHERE user_id=?",(session["user_id"],)).fetchall()
    db.close()
    linked_names = [r["bank_name"] for r in linked]
    return render_template("bank.html", linked=linked, linked_names=linked_names,
                           all_banks=list(MOCK_BANKS.keys()))

#Connect bank (mock) 
@app.route("/bank/connect", methods=["POST"])
def bank_connect():
    if login_required(): return redirect(url_for("login"))
    bank_name = request.form.get("bank_name","")
    if bank_name not in MOCK_BANKS:
        flash("Geçersiz banka","error"); return redirect(url_for("bank"))
    uid  = session["user_id"]
    data = MOCK_BANKS[bank_name]
    db   = get_db(); c = db.cursor()

    #Avoid duplicate links
    if c.execute("SELECT id FROM linked_accounts WHERE user_id=? AND bank_name=?",(uid,bank_name)).fetchone():
        db.close(); flash(f"{bank_name} zaten bağlı","error"); return redirect(url_for("bank"))

    #Save linked account
    c.execute("INSERT INTO linked_accounts(user_id,bank_name,account_no,balance) VALUES(?,?,?,?)",
              (uid,bank_name,data["account_no"],data["balance"]))

    #Import mock transactions
    for title, type_, amount in data["transactions"]:
        c.execute("INSERT INTO transactions(user_id,title,amount,type) VALUES(?,?,?,?)",(uid,title,amount,type_))

    db.commit(); db.close()
    flash(f"{bank_name} başarıyla bağlandı! {len(data['transactions'])} işlem aktarıldı.","success")
    return redirect(url_for("bank"))

#Disconnect bank 
@app.route("/bank/disconnect", methods=["POST"])
def bank_disconnect():
    if login_required(): return redirect(url_for("login"))
    bank_name = request.form.get("bank_name","")
    uid = session["user_id"]
    db  = get_db(); c = db.cursor()
    c.execute("DELETE FROM linked_accounts WHERE user_id=? AND bank_name=?",(uid,bank_name))
    # Remove imported transactions for this bank
    c.execute("DELETE FROM transactions WHERE user_id=? AND title LIKE ?",(uid,f"%-{bank_name.split()[0]}%"))
    db.commit(); db.close()
    flash(f"{bank_name} bağlantısı kesildi","success"); return redirect(url_for("bank"))

#Calculator page 
@app.route("/calculator")
def calculator():
    if login_required(): return redirect(url_for("login"))
    return render_template("calculator.html")

if __name__ == "__main__":
    app.run(debug=True)

#Language switcher 
@app.route("/set_lang", methods=["POST"])
def set_lang():
    lang = request.form.get("lang","tr")
    if lang in ("tr","en"):
        session["lang"] = lang
    return redirect(request.referrer or url_for("dashboard"))
