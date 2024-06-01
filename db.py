from flask import Flask, render_template, request, redirect,url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__, template_folder='./templates', static_folder='./static')

app.secret_key='1234'

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='rentease'
app.config['MYSQL_PASSWORD']='rentease123'
app.config['MYSQL_DB']='rentease'

mysql=MySQL(app)


@app.route('/') 
def home():
    return render_template('home.html')

@app.route('/register',methods=['GET','POST'])
def reg():
    if request.method=='POST':
        pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        userfname=request.form['fname']
        userlname=request.form['lname']
        contactno=request.form['contact']
        email=request.form['email']
        password=request.form['pass']
        cpassword=request.form['c_pass']
        username=userfname+' '+userlname
        val=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        val.execute(f"SELECT `checkreg`('{email}')")
        check=val.fetchall()
        val.close()
        num=check[0]
        str=f"`checkreg`('{email}')"
        x=num[str]
        if x>=1:
            msg='Entered email is already registered, Try with another email'
            return render_template('register.html',msg=msg)
        
        # val.execute(f"SELECT * FROM user")
        # check=val.fetchall()
        # val.close()
        # for mail in check:
        #     if  email==mail['email_id']:
        #         msg='Entered email is already registered, Try with another email'
        #         return render_template('register.html',msg=msg)


        if userfname.isalpha() and userlname.isalpha():
            if contactno.isdigit():
                if re.match(pat,email):
                    if(password==cpassword):
                        cur=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                        cur.execute(f"CALL InsertUser('{username}', '{contactno}', '{email}', '{password}');")
                        #cur.execute(f"INSERT INTO user(u_name,u_contactno,email_id,password) VALUES('{username}','{contactno}','{email}','{password}')")
                        mysql.connection.commit()
                        cur.close()
                        return redirect('/login')
                    else:
                        msg='Entered passwords do not match'
                        return render_template('register.html',msg=msg)
                else:
                    msg='Enter a valid email'
                    return render_template('register.html',msg=msg)
            else:
                msg='Enter a valid contact number'
                return render_template('register.html',msg=msg)    
        else:
            msg='Enter a valid name containing alphabets and no spaces'
            return render_template('register.html',msg=msg)
           
    return render_template('register.html')




@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        val=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        val.execute(f"SELECT * FROM user")
        check=val.fetchall()
        val.close()
        email=request.form['email']
        password=request.form['pass']
        if re.match(pat,email):
            for mail in check:
                if  email==mail['email_id']: 
                    if password==mail['password']:
                        return redirect('/listings')
                    else:
                        msg='Wrong password'
                        return render_template('login.html',msg=msg)
            msg='Email not registered'
            return render_template('login.html',msg=msg)
        else:
            msg='Enter a valid email'
            return render_template('login.html',msg=msg)
    return render_template('login.html')


@app.route('/listings', methods=['GET', 'POST'])
def listing():


    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM house h JOIN owners o ON h.o_id = o.o_id")
    original_houses = cursor.fetchall()
    session['original_houses'] = original_houses
    cursor.close()


    filtered_houses = session.pop('filtered_houses', None)  # Remove filtered_houses from session
    houses = original_houses if filtered_houses is None else filtered_houses
   

    if request.method == 'GET':
        search = request.args.get("searchbar")
        if search:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(f"SELECT * FROM house NATURAL JOIN owners WHERE a_name = '{search}' ")
            houses = cursor.fetchall()
            cursor.close()
            #return render_template('listings.html', Houses=houses)
            if search == "highest rated":
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute(f"select * from house h natural join owners o join feedback using(a_name,house_no,block) where ratings>=all(select max(ratings) from house join feedback using(a_name,house_no,block));")
                houses = cursor.fetchall()
                cursor.close()
            return render_template('listings.html', Houses=houses)


    if request.method == 'POST':
        block_no = request.form['block_no']
        a_name = request.form['a_name']
        house_no = request.form['house_no']
        return redirect(url_for('view_property', block_no=block_no, a_name=a_name, house_no=house_no))
    session['original_houses'] = houses
    return render_template('listings.html', Houses=houses)


@app.route('/filter', methods=['GET', 'POST'])
def filter():
    l = ['Pool', 'Gym', 'Parking', 'Clubhouse']
    if request.method == 'POST':
        sort = request.form.get('sort')
        amenities = request.form.getlist('amecheckbox')
        bhk = request.form.getlist('bhkcheckbox')

        query = "SELECT * FROM house h JOIN owners o USING (o_id) WHERE 1=1 "
        for bhk_val in bhk:
            query += f" AND bhk = {bhk_val}"

        if amenities:
            query += " AND a_name in (SELECT a_name FROM amenities WHERE 1=1 "
            for amenity in amenities:
                query += f" AND {amenity} = 1"
            query += ")"

        if sort == 'asc':
            query += " ORDER BY rent ASC"
        elif sort == 'desc':
            query += " ORDER BY rent DESC"

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(query)
        filtered_houses = cursor.fetchall()
        session['filtered_houses'] = filtered_houses
        cursor.close()
        return redirect(url_for('listing', Houses=filtered_houses, original_houses=session.get('original_house'))) 
        #return render_template('listings.html', Houses=filtered_houses, original_houses=session.get('original_house'))
    return render_template('filtersort.html', l=l)



@app.route('/view_property')
def view_property():
    
    block_no = request.args.get('block_no')
    a_name = request.args.get('a_name')
    house_no = request.args.get('house_no')

    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(f"select * from house h join owners o on h.o_id = o.o_id where h.block = '{block_no}' AND  h.a_name = '{a_name}' AND h.house_no = '{house_no}';")
    house = cursor.fetchone()
    cursor.close()
    
    bid = house['b_id']
    rent = house['rent']


    recur=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    recur.execute(f"SELECT * FROM feedback WHERE house_no='{house_no}'")
    re=recur.fetchone()
    recur.close()

    brocur=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    brocur.execute(f"select * from broker natural join house where b_id = {bid} ")
    bro=brocur.fetchone()
    b=bro['brokerage']
    bfee=int((b/100)*rent)


    loccur=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    loccur.execute(f"select * from location natural join apartment WHERE a_name='{a_name}'")
    loc=loccur.fetchone()
    loccur.close()

    cur=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(f"SELECT * FROM amenities WHERE a_name= '{a_name}'")
    ame=cur.fetchone()
    cur.close()
    l=[]
    if ame['pool']==1:
        l.append('Pool')
    if ame['gym']==1:
        l.append('Gym')
    if ame['lift']==1:
        l.append('Lift')
    if ame['parking']==1:
        l.append('Parking')
    if ame['power_backup']==1:
        l.append('Power Backup')
    if ame['clubhouse']==1:
        l.append('Clubhouse')

    rent=house['rent']
    expense= (rent*12)+bfee+(3500*12)+(rent*2)
    

    return render_template('view_property.html', House = house, l = l, bfee = bfee, bro = bro, loc = loc, re=re, expense = expense)

if(__name__ == '__main__'):
    app.run(port=8000, debug = True)