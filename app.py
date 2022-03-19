#IMPORTING LIBRARIES
from flask import request,render_template,Flask,redirect,flash,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import matplotlib.pyplot as plt
import numpy as np

#CONFIGURING THE APPLICATION
app = Flask(__name__)
app.config.update(SECRET_KEY=os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#DATABASE CREATION
class user(db.Model):
    __name__ = "user"
    user_id = db.Column(db.Integer,autoincrement=True, primary_key=True)
    username = db.Column(db.String(80),nullable=False)
    mail = db.Column(db.Text,nullable=False)
    password = db.Column(db.Text,nullable=False)

class tracker(db.Model):
    __name__ = "tracker"
    u_name = db.Column(db.String(80),db.ForeignKey('user.username'),nullable=False)
    tracker_id = db.Column(db.Integer,autoincrement=True,primary_key=True,nullable=False)
    tracker_name = db.Column(db.String(80),nullable=False)
    tracker_description = db.Column(db.String(100))
    tracker_type = db.Column(db.String(40),nullable=False)
    tracker_settings = db.Column(db.String(40))

class logtable(db.Model):
    log_id = db.Column(db.Integer,primary_key=True,nullable=False,autoincrement=True)
    user_name = db.Column(db.String(80),db.ForeignKey('user.username'),nullable=False)
    t_id = db.Column(db.Integer,db.ForeignKey('tracker.tracker_id'),nullable=False)
    Timestamp = db.Column(db.DateTime,nullable=False, default = datetime.utcnow())
    value = db.Column(db.Text,nullable=False)
    Note = db.Column(db.String(80))

#LOGIN PAGE
@app.route('/', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        name = request.form.get('uname')
        passw = request.form.get('passw')
        existing = user.query.all()
        flag ='False'
        for i in existing:
            if(i.username==str(name) and i.password==str(passw)):
                flag='True'
        if(flag=='True'):
            return redirect('/home/{0}'.format(name))
        else:
            return render_template('login.html',name=name,flag=flag)
    return render_template('login.html')

#REGISTRATION PAGE
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method=='POST':
        mail = request.form['mailID']
        name = request.form['uname']
        password = request.form['passw']
        user1 = user(mail = mail,username=name,password=password)
        existing = user.query.all()
        flag2 = 'False'
        for i in existing:
            if(i.username==name and i.mail == mail):
                flag2 = 'True'
        if(flag2=='True'):
            flash('This username is already registered')
            return redirect('/')
        else:
            db.session.add(user1)
            db.session.commit()
            return redirect('/home/{}'.format(name))
        return redirect('/home/{0}'.format(name))
    return render_template('register.html')

#HOME PAGE
@app.route('/home/<string:name>')
def guest(name):
    return render_template('home.html', name=name)

#TRACKERS PAGE
@app.route('/trackers/<string:name>', methods=['GET', 'POST'])
def u_tracker(name):
    table = tracker.query.filter_by(u_name=name).all()
    return render_template('trackers.html',name=name,table=table)

#TRACKERS CREATION PAGE
@app.route('/trackers/<string:name>/create',methods=['GET','POST'])
def create_tracker(name):
    if request.method=='POST':
        tname = request.form.get('tname')
        ttype = request.form.get('ttype')
        tdesc = request.form.get('tdesc')
        tsettings = request.form.get('tsettings')
        track = tracker(tracker_name=tname,tracker_type=ttype,tracker_description=tdesc,u_name=name,tracker_settings=tsettings)
        db.session.add(track) 
        db.session.commit()
        return redirect('/trackers/{0}'.format(name))
    return render_template('t_create.html',name=name)

#DELETE TRACKER PAGE
@app.route('/trackers/<int:id>/<string:name>/Delete')
def delete(id,name):
    deletable = tracker.query.filter_by(tracker_id=id).first()
    deletable1 = logtable.query.filter_by(t_id=id).all()
    for i in deletable1:
        db.session.delete(i)
    db.session.delete(deletable)
    db.session.commit()
    return redirect('/trackers/{}'.format(name))

#UPDATE TRACKER PAGE
@app.route('/trackers/<int:id>/<string:name>/Update', methods=['GET', 'POST'])
def update_tracker(id,name):
    data = tracker.query.filter_by(tracker_id=id,u_name=name).first()
    if(request.method=='POST'):
        tname = request.form.get('tname')
        ttype = request.form.get('ttype')
        tdesc = request.form.get('tdesc')
        tsettings = request.form.get('tsettings')
        data.tracker_name = tname
        data.tracker_type = ttype
        data.tracker_description = tdesc
        data.tracker_settings = tsettings
        db.session.add(data)
        db.session.commit()
        return redirect('/trackers/{0}'.format(name))
    return render_template('update.html',data=data,name=name,id=id)

#LOGGING PAGE
@app.route('/trackers/<int:id>/<string:name>/log', methods=['GET', 'POST'])
def log(id,name):
    cell = tracker.query.filter_by(u_name=name,tracker_id=id).first()
    l = cell.tracker_settings.split(',')

    if request.method=='POST':
        val = request.form['value']
        note = request.form.get('Note')
        
        cell = logtable(user_name=name,t_id=id,Note=note,value=val)
        db.session.add(cell)
        db.session.commit()
        return redirect('/trackers/{}'.format(name))
    return render_template('log.html',cell=cell,l=l,name=name,id=id)

#TRACKER INFO PAGE
@app.route('/trackers/<int:id>/<string:name>/info')
def info(id,name):
    data = logtable.query.filter_by(t_id=id).all()
    tracker_info = tracker.query.filter_by(tracker_id=id).first()
    l=[]
    d={}
    if(len(data)!=0):
        if(tracker_info.tracker_type=='Numerical'):
            for i in data:
                l.append(float(i.value))
            val = np.array(l)
            plt.hist(val)   
            plt.title('Progress')
            plt.xlabel(tracker_info.tracker_name)
            plt.ylabel('Value')
            plt.savefig('static/plot.png',dpi=300)
            plt.close()

        else:
            for i in data:
                if(i.value not in d.keys()):
                    d[i.value] = 1
                else:
                    d[i.value]+=1
            plt.bar(list(d.keys()), d.values(), color='b')   
            plt.title('Progress')
            plt.xlabel(tracker_info.tracker_name)
            plt.ylabel('Value')
            plt.savefig('static/plot.png',dpi=300)
            plt.close()   
    return render_template('info.html',data=data,name=name,id=id,tinfo=tracker_info)

#DELETE LOGS PAGE
@app.route('/log/<int:id>/<string:name>/<int:tid>/Delete')
def deleteLog(id,name,tid):
    deletable = logtable.query.filter_by(log_id=id,t_id=tid).first()
    db.session.delete(deletable)
    db.session.commit()
    return redirect('/trackers/{0}/{1}/info'.format(tid,name))

#UPDATE LOG PAGE
@app.route('/log/<int:id>/<string:name>/<int:tid>/Update',methods=['GET','POST'])
def updateLog(id,name,tid):
    data = logtable.query.filter_by(log_id=id,t_id=tid).first()
    tinfo = tracker.query.filter_by(tracker_id=tid,u_name=name).first()
    l = tinfo.tracker_settings.split(',')
    if request.method=='POST':
        ts = datetime.utcnow()
        data.Note = request.form.get('Note')
        data.value = request.form["value"]
        data.Timestamp = ts
        db.session.add(data)
        db.session.commit()
        return redirect('/trackers/{0}/{1}/info'.format(tid,name))
    return render_template('updatel.html',data=data,tinfo=tinfo,l=l,id=id,name=name,tid=tid)

#ABOUT PAGE
@app.route('/about/<string:name>')
def about(name):
    return render_template('about.html',name=name)

#MAIN
if __name__ == "__main__":
    app.run()