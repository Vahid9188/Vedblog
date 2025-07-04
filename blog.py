from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb  import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


# Kullancı giriş Dekoreatoru
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      if "logged_in" in session:
          return f(*args, **kwargs)
      else:
          flash("Bu sayfayı görüntülemek için lütfen giriş yapın ....","danger")
          return redirect(url_for("login"))
        
    return decorated_function


class RegisteForm(Form):
    name=StringField("İsim Soyisim:",validators=[validators.Length(min=4,max=25)])
    username=StringField("Kullancı adı:",validators=[validators.Length(min=5,max=35)])
    email=StringField("E-mail adresi:",validators=[validators.Email(message="Lütfen e-mail adresini doğru girin...")])
    password=PasswordField("Şifre:",validators=[
        validators.DataRequired(message="Bir şifre girin"),
        validators.EqualTo(fieldname="confirm",message="Şifre doğru yazılmamış...")
    ] )
    confirm=PasswordField("Şifreni Doğrula:")

class LoginForm(Form):
    username=StringField("Kullancı adı:")
    password=PasswordField("Şifre:")

app = Flask(__name__)
app.secret_key = 'vahid9188'


app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="history"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql= MySQL(app)



@app.route("/")
def index():
   return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles"
    result=cursor.execute(sorgu)
    if result > 0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html", articles=[])

@app.route("/dashboard")
@login_required
def dashboard():


    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author=%s"
    result=cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisteForm(request.form)

    if request.method == "POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()
        

       
        

        sorgu="INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu, (name, email, username, password))  
        mysql.connection.commit()
        cursor.close()     
        flash("Qeydiyyat uğurla başa çatdı!", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login",methods=["GET","POST"])
def login():
     form=LoginForm(request.form)
     if request.method == "POST":
         username=form.username.data
         password_entered=form.password.data

         cursor=mysql.connection.cursor()

         sorgu="Select * from users  where username = %s"

         result=cursor.execute(sorgu,(username,))

         if result > 0:
             data=cursor.fetchone()
             real_password=data["password"]
             if sha256_crypt.verify(password_entered,real_password):
                 flash("Başarıyla giriş yapdınız","success")

                 session["logged_in"]=True
                 session["username"]=username
                 return redirect(url_for("index"))
             else:
                 flash("Parolanızı yanlış girdiniz...","danger")
                 return redirect(url_for("index"))        
                 
         else:
             flash("Böyle bir kullancı bulunmuyor... ","danger")
             return redirect(url_for("login"))

     return render_template("login.html",form=form)
#Detay sayfası
@app.route("/article/<string:id>")
def view_article(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where id=%s"
    result=cursor.execute(sorgu,(id,))
    if result > 0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/addarticle",methods=["GET","POST"])
@login_required
def add_articles():
    form=ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title=form.title.data
        content=form.content.data

        cursor=mysql.connection.cursor()
        sorgu="INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale oluşturuldu","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)
#makale silme

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author=%s and id=%s"
    result=cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2="Delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Boyle bir makale yok","danger")
        return redirect(url_for("index"))
    
#makale güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required 
def update(id):
    if request.method == "POST":
        title=request.form["title"]
        content=request.form["content"]

        cursor=mysql.connection.cursor()
        sorgu="Update articles set title=%s,content=%s where id=%s"
        cursor.execute(sorgu,(title,content,id))
        mysql.connection.commit()
        cursor.close()
        flash("Makale güncellendi","success")
        return redirect(url_for("dashboard"))
    else:
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where id=%s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))
        if result > 0:
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)
        else:
            flash("Boyle bir makale yok","danger")
            return redirect(url_for("index"))
        


class ArticleForm(Form):
    title=StringField("Makale Baslığı:",validators=[validators.Length(min=5,max=100)])
    content=TextAreaField("Makale Içerği:",validators=[validators.Length(min=10)])
#arama
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE title LIKE %s"
        keyword = f"%{keyword}%"
        result = cursor.execute(sorgu, (keyword,))

        if result == 0:
            flash("Aradıgınız makale bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)

if __name__ == "__main__":
    app.run(debug=True)

